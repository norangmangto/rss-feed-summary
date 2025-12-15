import argparse
from .cli import run_once, run_scheduler, check_feeds, clean_feeds


def main():
    parser = argparse.ArgumentParser(description="RSS Feed Summarizer")
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    parser.add_argument("--dry-run", action="store_true", help="Render and print email instead of sending")
    parser.add_argument("--subject-date", action="store_true", help="Append current date to subject")
    parser.add_argument("--plain-text", action="store_true", help="Include text/plain alternative body")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("once", help="Fetch, summarize, and send once")
    subparsers.add_parser("schedule", help="Run daily scheduler")
    subparsers.add_parser("check", help="Check RSS feed URLs for availability")
    clean_parser = subparsers.add_parser("clean", help="Remove dead feeds from config")
    clean_parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")

    args = parser.parse_args()
    if args.command == "schedule":
        # scheduler uses config only; dry-run isn't meaningful here
        run_scheduler(args.config)
    elif args.command == "check":
        check_feeds(args.config)
    elif args.command == "clean":
        clean_feeds(args.config, force=args.force)
    else:
        run_once(args.config, dry_run=args.dry_run, subject_date=args.subject_date, plain_text=args.plain_text)


if __name__ == "__main__":
    main()