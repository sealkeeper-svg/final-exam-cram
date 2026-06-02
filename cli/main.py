import sys
import os
from datetime import date, datetime
import questionary
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.align import Align
from rich.text import Text
from rich.box import HEAVY, ROUNDED

from crammer.config import load_config, get_api_key, setup_api_key
from crammer.db.store import (
    init_db, add_subject, get_subject, list_subjects,
    add_chapter, add_knowledge_point, get_chapters, get_knowledge_points,
    get_cards, get_calc_problems,
)
from crammer.parser.pdf_parser import parse_pdf
from crammer.parser.pptx_parser import parse_pptx
from crammer.extractor.chunker import scan_folder, chunk_documents
from crammer.extractor.knowledge_tree import build_knowledge_tree, confirm_chapters, extract_metadata
from crammer.extractor.card_generator import generate_cards_for_subject
from crammer.scheduler.spaced_repetition import get_subject_dashboard, get_due_cards, get_due_calc_problems, update_kp_after_review
from crammer.review.daily_review import start_daily_review, record_review_result
from crammer.review.quiz_mode import generate_quiz, score_quiz
from crammer.review.cram_mode import get_cram_flash_cards, get_key_points, get_error_redo_cards
from crammer.review.guided_learning import build_learning_paths, format_step_for_display

console = Console()
DB_PATH = "data/crammer.db"


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def header(subtitle=None):
    clear()
    console.print(Align.center(Text("FINAL EXAM CRAM", style="bold cyan")))
    if subtitle:
        console.print(Align.center(Text(subtitle, style="dim")))
    console.print()


def ensure_setup():
    init_db(DB_PATH)
    config = load_config()
    if not config.get("api_key"):
        header("First Time Setup")
        console.print(Panel(
            "Welcome! You need a DeepSeek API Key to generate study materials.\n"
            "Get one at [link]https://platform.deepseek.com[/]\n"
            "Cost: ~0.5-1 CNY per subject (200-page courseware)",
            border_style="cyan"
        ))
        console.print()
        setup_api_key()
    return True


def menu_new_subject():
    header("New Subject")

    name = questionary.text("Subject name:", validate=lambda x: len(x.strip()) > 0).ask()
    if not name:
        return

    exam_str = questionary.text("Exam date (YYYY-MM-DD):", default=date.today().strftime("%Y-%m-%d")).ask()
    try:
        exam_date = datetime.strptime(exam_str, "%Y-%m-%d").date()
    except ValueError:
        console.print("[red]Invalid date format[/]")
        questionary.confirm("Press Enter to return...").ask()
        return

    folder = questionary.path("Courseware folder path:").ask()
    if not folder or not os.path.isdir(folder):
        console.print("[red]Folder not found[/]")
        questionary.confirm("Press Enter to return...").ask()
        return

    files = scan_folder(folder)
    if not files:
        console.print("[red]No PDF or PPTX files found in this folder[/]")
        questionary.confirm("Press Enter to return...").ask()
        return

    console.print(f"\n  Found [cyan]{len(files)}[/] files:")
    for f in files:
        console.print(f"    [dim]{os.path.basename(f)}[/]")
    console.print()

    if not questionary.confirm("Start parsing?").ask():
        return

    subject = add_subject(name, exam_date, db_path=DB_PATH)
    subject_id = subject.id

    parsed_files = []
    with console.status(f"[cyan]Parsing {len(files)} files...", spinner="dots"):
        for fp in files:
            if fp.endswith('.pdf'):
                parsed_files.append(parse_pdf(fp))
            else:
                parsed_files.append(parse_pptx(fp))
    console.print(f"  [green]Parsed {len(parsed_files)} files[/]")

    with console.status("[cyan]Chunking...", spinner="dots"):
        chunks = chunk_documents(parsed_files)
    console.print(f"  [green]{len(chunks)} chunks created[/]")

    progress = {"current": 0, "total": len(chunks)}
    def on_progress(cur, total, chunk_id):
        progress["current"] = cur
        progress["total"] = total

    api_key = get_api_key()
    console.print(f"\n  [cyan]DeepSeek: building knowledge tree ({len(chunks)} chunks)...[/]")
    with console.status("[cyan]Calling DeepSeek...", spinner="dots"):
        tree = build_knowledge_tree(chunks, name, subject_id, api_key=api_key, on_progress=on_progress, db_path=DB_PATH)

    meta = extract_metadata(tree)
    console.print(f"  [green]Knowledge tree: {meta['chapter_count']} chapters, {meta['kp_count']} knowledge points[/]")
    console.print()

    chapters = get_chapters(subject_id, db_path=DB_PATH)
    active_chapters = [c for c in chapters if c.status == 'active']
    if active_chapters:
        choices = [questionary.Choice(f"{ch.title} ({get_knowledge_points(ch.id, db_path=DB_PATH).__len__()} kps)", checked=True, value=ch.order - 1) for ch in active_chapters]
        selected = questionary.checkbox(
            "Select chapters to KEEP (uncheck to skip):",
            choices=choices
        ).ask()
        if selected is not None:
            tree = confirm_chapters(tree, selected, db_path=DB_PATH)
            console.print(f"  [green]Kept {len(selected)} chapters[/]")
        console.print()

    with console.status("[cyan]DeepSeek: generating cards...", spinner="dots"):
        result = generate_cards_for_subject(subject_id, api_key=api_key, db_path=DB_PATH)
    console.print(f"  [green]Concept cards: {result['concept_cards']}[/]")
    console.print(f"  [green]Calc problems: {result['calc_problems']}[/]")
    if result['calc_unmatched'] > 0:
        console.print(f"  [yellow]Unmatched calc types: {result['calc_unmatched']} (AI fallback needed)[/]")

    console.print()
    console.print(f"[bold green]Subject '{name}' is ready![/]")
    console.print(f"  Exam: {exam_date}  |  {(exam_date - date.today()).days} days remaining")
    questionary.confirm("Press Enter to return...").ask()


def menu_subject_dashboard(subject):
    sid = subject.id
    dash = get_subject_dashboard(sid, db_path=DB_PATH)

    while True:
        header(f"{subject.name} — Dashboard")
        days = dash['days_until_exam']

        table = Table(box=ROUNDED, show_header=False)
        table.add_column("", style="cyan")
        table.add_column("", style="white")
        table.add_row("Exam", f"{subject.exam_date} [{'red' if days <= 3 else 'yellow' if days <= 7 else 'dim'}]({days} days)[/]")
        table.add_row("Mastery", f"{ProgressBar(total=100, completed=int(dash['mastery_pct']), width=20)} {dash['mastery_pct']}%")
        table.add_row("Cards", f"{dash['reviewed_cards']}/{dash['total_cards']} reviewed")
        table.add_row("Due Today", f"[bold magenta]{dash['due_cards_today']} cards[/]")
        console.print(table)
        console.print()

        action = questionary.select(
            "What to do?",
            choices=[
                questionary.Choice("Guided Learning — step-by-step concept walkthrough", value="learn"),
                questionary.Choice("Daily Review — card-by-card memory practice", value="review"),
                questionary.Choice("Quiz Mode — timed exam simulation", value="quiz"),
                questionary.Choice("Cram Mode — last-minute rapid review", value="cram"),
                questionary.Choice("Back", value="back"),
            ]
        ).ask()

        if action == "back":
            break
        elif action == "learn":
            menu_guided_learning(sid)
        elif action == "review":
            menu_daily_review(sid)
        elif action == "quiz":
            menu_quiz(sid)
        elif action == "cram":
            menu_cram(sid)


def menu_guided_learning(subject_id):
    paths = build_learning_paths(subject_id, db_path=DB_PATH)
    if not paths:
        console.print("[yellow]No learning paths available — generate cards first[/]")
        questionary.confirm("Press Enter to return...").ask()
        return

    subject = get_subject(subject_id, db_path=DB_PATH)
    while True:
        header(f"Guided Learning — {subject.name}")
        choices = [questionary.Choice(f"{p.title}  [dim]({len(p.steps)} steps)[/]", value=p.path_id) for p in paths]
        choices.append(questionary.Choice("Back", value="back"))
        choice = questionary.select("Select a learning path:", choices=choices).ask()
        if choice == "back":
            break

        path = next((p for p in paths if p.path_id == choice), None)
        if not path:
            continue

        for step in path.steps:
            header(f"Guided Learning — {path.title}")
            console.print(Panel(f"[bold yellow]{step.title}[/]", border_style="yellow", box=HEAVY))
            console.print()
            console.print(Panel(step.explanation, border_style="cyan", padding=(1, 2)))
            console.print()
            questionary.confirm("Understood? Press Enter to continue...").ask()
            console.print()
            console.print(Panel(f"[bold]Check Yourself:[/]\n{step.check_question}", border_style="magenta", padding=(1, 2)))
            questionary.confirm("Think, then Enter for answer...").ask()
            console.print()
            console.print(Panel(f"[green]{step.check_answer}[/]", border_style="green", padding=(1, 2)))
            console.print(f"  [bold yellow]Key Insight:[/] [dim]{step.insight}[/]")
            console.print()

            nxt = questionary.select("Next:", choices=["Continue", "Re-read", "Quit path"]).ask()
            if nxt == "Re-read":
                questionary.confirm("Press Enter to re-read...").ask()
            elif nxt == "Quit path":
                break

        console.print()
        console.print("[bold green]Path complete![/]")


def menu_daily_review(subject_id):
    subject = get_subject(subject_id, db_path=DB_PATH)
    session = start_daily_review(subject_id, db_path=DB_PATH)

    if session['total_due'] == 0:
        console.print("[green]Nothing due today! You're caught up.[/]")
        questionary.confirm("Press Enter to return...").ask()
        return

    cards = session['cards']
    calc_problems = session['calc_problems']
    all_items = [(c, kp, 'card') for c, kp in cards] + [(p, kp, 'calc') for p, kp in calc_problems]

    correct = 0
    total = len(all_items)

    for i, (item, kp, kind) in enumerate(all_items, 1):
        header(f"Daily Review — {subject.name}  [{i}/{total}]")

        if kind == 'card':
            q = item.question
            a = item.answer
            card_id = item.id
            calc_id = None
        else:
            q = item.question_text
            a = item.answer_text
            card_id = None
            calc_id = item.id

        console.print(Panel(f"[bold white]{q}[/]", border_style="cyan", padding=(1, 2)))
        console.print()
        questionary.confirm("Press Enter for answer...").ask()
        console.print()
        console.print(Panel(f"[green]{a}[/]", border_style="green", padding=(1, 2)))
        console.print()

        result = questionary.select("Self-check:", choices=["Pass — I knew it", "Fail — I forgot"]).ask()
        is_pass = "Pass" in result
        if is_pass:
            correct += 1

        record_review_result(
            card_id=card_id, calc_problem_id=calc_id,
            kp_id=kp.id, result="pass" if is_pass else "fail",
            exam_date=subject.exam_date, db_path=DB_PATH
        )

    header(f"Daily Review — {subject.name}")
    console.print(f"\n[bold green]Done! Accuracy: {correct}/{total} = {round(correct/total*100)}%[/]")
    questionary.confirm("Press Enter to return...").ask()


def menu_quiz(subject_id):
    subject = get_subject(subject_id, db_path=DB_PATH)
    quiz = generate_quiz(subject_id, db_path=DB_PATH)

    if quiz['total'] == 0:
        console.print("[yellow]No cards available for quiz — generate cards first[/]")
        questionary.confirm("Press Enter to return...").ask()
        return

    user_results = []
    for i, q in enumerate(quiz['questions'], 1):
        header(f"Quiz — {subject.name}  [{i}/{quiz['total']}]")
        console.print(f"[dim]{q['type']}[/]")
        console.print(Panel(f"[bold white]{q['question']}[/]", border_style="cyan", padding=(1, 2)))
        console.print()
        questionary.confirm("Press Enter for answer...").ask()
        console.print()
        console.print(Panel(f"[green]{q['answer']}[/]", border_style="green", padding=(1, 2)))
        console.print()

        result = questionary.select("Result:", choices=["Correct", "Wrong"]).ask()
        user_results.append({"correct": result == "Correct", "time_spent": 0, "kp_id": 1})

    scored = score_quiz(quiz['questions'], user_results, subject_id, db_path=DB_PATH)
    header(f"Quiz Results — {subject.name}")
    score_table = Table(box=HEAVY)
    score_table.add_column("Score", style="bold yellow", justify="center")
    score_table.add_column("Accuracy", style="bold green", justify="center")
    score_table.add_column("Errors", style="bold red", justify="center")
    score_table.add_row(f"{scored['score']}/{scored['total']}", f"{scored['accuracy']}%", str(len(scored['wrong_questions'])))
    console.print(score_table)
    questionary.confirm("Press Enter to return...").ask()


def menu_cram(subject_id):
    subject = get_subject(subject_id, db_path=DB_PATH)

    while True:
        header(f"Cram Mode — {subject.name}")
        console.print(Panel(f"Exam in [bold red]{(subject.exam_date - date.today()).days} days[/]", border_style="red", box=HEAVY))
        console.print()

        mode = questionary.select(
            "Select cram mode:",
            choices=[
                questionary.Choice("Flash Scan — rapid pass through all cards", value="flash"),
                questionary.Choice("Key Points — formulas + core concepts + pitfalls", value="key"),
                questionary.Choice("Error Redo — only review wrong answers", value="error"),
                questionary.Choice("Back", value="back"),
            ]
        ).ask()

        if mode == "back":
            break
        elif mode == "flash":
            cards = get_cram_flash_cards(subject_id, db_path=DB_PATH)
            if not cards:
                console.print("[yellow]No cards yet[/]")
                questionary.confirm("Press Enter...").ask()
                continue
            for i, c in enumerate(cards, 1):
                header(f"Flash Scan — [{i}/{len(cards)}]")
                console.print(Panel(f"[bold white]{c['question']}[/]", border_style="cyan", padding=(1, 2)))
                questionary.confirm("Enter for answer...").ask()
                console.print(Panel(f"[green]{c['answer']}[/]", border_style="green", padding=(1, 2)))
                console.print(f"[dim]Mastery: {int(c['mastery']*100)}%[/]")
                console.print("[dim]---[/]")

        elif mode == "key":
            kp = get_key_points(subject_id, db_path=DB_PATH)
            console.print(Panel("KEY FORMULAS", border_style="cyan"))
            for f in kp['formulas']:
                console.print(f"  * {f}")
            console.print()
            console.print(Panel("ADVANCED CONCEPTS", border_style="yellow"))
            for cc in kp['core_concepts']:
                console.print(f"  * [bold]{cc['name']}[/]: {cc['content'][:80]}...")
            console.print()
            console.print(Panel("HIGH-ERROR TOPICS", border_style="red"))
            for he in kp['high_error_kps']:
                console.print(f"  * {he['name']}  [red]({he['error_count']} errors)[/]")
            questionary.confirm("Press Enter to return...").ask()

        elif mode == "error":
            cards = get_error_redo_cards(subject_id, db_path=DB_PATH)
            if not cards:
                console.print("[green]No errors — you're clean![/]")
                questionary.confirm("Press Enter to return...").ask()
                continue
            for c in cards:
                console.print(Panel(f"[bold white]{c['question']}[/]", border_style="red", padding=(1, 2)))
                questionary.confirm("Enter for answer...").ask()
                console.print(Panel(f"[green]{c['answer']}[/]", border_style="green", padding=(1, 2)))
                console.print(f"[red]Errored {c['error_count']} times[/]")
                console.print("[dim]---[/]")
            questionary.confirm("Press Enter to return...").ask()


def main():
    ensure_setup()

    while True:
        header(f"{date.today().strftime('%Y-%m-%d')}")
        subjects = list_subjects(include_archived=False, db_path=DB_PATH)

        if subjects:
            console.print("[bold]Your Subjects:[/]")
            console.print()
            table = Table(box=ROUNDED, show_header=True, header_style="bold white")
            table.add_column("#", justify="center", style="cyan")
            table.add_column("Subject", style="cyan")
            table.add_column("Exam", style="yellow")
            table.add_column("Mastery", width=24)
            table.add_column("Due", justify="center")

            today = date.today()
            for i, s in enumerate(subjects, 1):
                days = (s.exam_date - today).days if s.exam_date else 0
                dash = get_subject_dashboard(s.id, db_path=DB_PATH)
                bar = ProgressBar(total=100, completed=int(dash['mastery_pct']), width=16)
                urgency = "[red]!!" if days <= 3 else "[yellow]!" if days <= 7 else ""
                table.add_row(
                    str(i),
                    s.name,
                    f"{s.exam_date} {urgency}({days}d)",
                    f"{bar} {dash['mastery_pct']}%",
                    f"[bold magenta]{dash['due_cards_today']}[/]"
                )
            console.print(table)
            console.print()

            choices = []
            for i, s in enumerate(subjects, 1):
                days = (s.exam_date - date.today()).days if s.exam_date else 0
                tag = " [red]NEXT EXAM" if i == 1 else ""
                choices.append(questionary.Choice(f"{s.name} — {days}d left{tag}", value=str(s.id)))
            choices.append(questionary.Choice("New Subject", value="new"))
            choices.append(questionary.Choice("Quit", value="quit"))

            action = questionary.select("Select subject or action:", choices=choices).ask()
        else:
            console.print(Panel("No subjects yet. Create your first one!", border_style="yellow"))
            console.print()
            action = questionary.select(
                "Action:",
                choices=[
                    questionary.Choice("New Subject", value="new"),
                    questionary.Choice("Quit", value="quit"),
                ]
            ).ask()

        if action == "quit":
            break
        elif action == "new":
            menu_new_subject()
        elif action and action.isdigit():
            sid = int(action)
            subject = get_subject(sid, db_path=DB_PATH)
            if subject:
                menu_subject_dashboard(subject)

    console.print("[dim]Good luck on your exams![/]")


if __name__ == "__main__":
    main()
