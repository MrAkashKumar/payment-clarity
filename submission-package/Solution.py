"""Payment Clarity (Use Case 1) delivery entry point.
Uses the existing project implementation; keep this folder inside payment-clarity.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if not (PROJECT_ROOT / 'core' / 'investigation.py').is_file():
    raise RuntimeError('Keep submission-package inside the complete payment-clarity project.')
sys.path.insert(0, str(PROJECT_ROOT))
from agent.agent import run_agent as _run_agent
from core.investigation import investigate as _evidence

REQUIRED = {'question_id', 'payment_id', 'question', 'answer', 'citations', 'facts', 'tools_used'}


def investigate(question: str, payment_id: str, *, evidence_only: bool = False) -> dict:
    """Investigate a payment using the same core as the working application.

    With evidence_only=False, the configured live AI adapter is used. Its
    labelled evidence fallback is retained if an AI response fails validation.
    With evidence_only=True, no provider request is made.
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError('A non-empty payment investigation question is required.')
    if not isinstance(payment_id, str) or not payment_id.strip():
        raise ValueError('A payment ID is required.')
    return _evidence(payment_id, question) if evidence_only else _run_agent(question, payment_id)


def load_questions(path: Path) -> list[dict]:
    questions = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(questions, list) or not questions:
        raise ValueError('Questions must be a non-empty JSON array.')
    seen = set()
    for q in questions:
        if not isinstance(q, dict) or any(not isinstance(q.get(k), str) or not q[k].strip() for k in ('question_id', 'payment_id', 'question')):
            raise ValueError('Each question needs question_id, payment_id and question strings.')
        if q['question_id'] in seen:
            raise ValueError('Question IDs must be unique.')
        seen.add(q['question_id'])
    return questions


def validate_answers(answers: list, questions: list[dict]) -> None:
    if not isinstance(answers, list) or len(answers) != len(questions):
        raise ValueError('Answers must contain one result per question.')
    for answer, question in zip(answers, questions):
        if not isinstance(answer, dict) or not REQUIRED.issubset(answer):
            raise ValueError('Missing required payment answer fields.')
        if any(answer[k] != question[k] for k in ('question_id', 'payment_id', 'question')):
            raise ValueError('Answer identity/order does not match the supplied questions.')
        if not isinstance(answer['answer'], str) or not answer['answer'].strip():
            raise ValueError('An answer must contain non-empty text.')
        if not isinstance(answer['facts'], dict):
            raise ValueError('Answer facts must be an object.')
        for field in ('citations', 'tools_used'):
            if not isinstance(answer[field], list) or not all(isinstance(v, str) for v in answer[field]):
                raise ValueError(f'{field} must be an array of strings.')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--questions', type=Path, default=PROJECT_ROOT / 'questions' / 'questions.json')
    parser.add_argument('--output', type=Path, default=Path(__file__).with_name('answers.json'))
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--evidence-only', action='store_true', help='Run deterministic checks without provider calls.')
    source.add_argument('--snapshot', type=Path, help='Validate and package an existing run; does not rerun the model.')
    args = parser.parse_args()
    questions = load_questions(args.questions)
    if args.snapshot:
        answers = json.loads(args.snapshot.read_text(encoding='utf-8'))
    else:
        answers = []
        for q in questions:
            result = investigate(q['question'], q['payment_id'], evidence_only=args.evidence_only)
            result.update({k:q[k] for k in ('question_id', 'payment_id', 'question')})
            answers.append(result)
    validate_answers(answers, questions)
    args.output.write_text(json.dumps(answers, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(f'Wrote {len(answers)} payment investigation answers to {args.output}')


if __name__ == '__main__':
    main()
