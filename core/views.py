from django.shortcuts import render, get_object_or_404
from .models import Concept
from .forms import QuestionForm
from .ai import answer_stats_question

MAX_HISTORY = 5  # how many past Q&As to keep in session


def home(request):
    return render(request, 'core/home.html')


def concepts_list(request):
    concepts = Concept.objects.all()
    level = request.GET.get('level')
    if level in ['beginner', 'intermediate', 'advanced']:
        concepts = concepts.filter(level=level)
    return render(request, 'core/concepts_list.html', {'concepts': concepts})


def concept_detail(request, slug):
    concept = get_object_or_404(Concept, slug=slug)
    return render(request, 'core/concept_detail.html', {'concept': concept})


def ask(request):
    form = QuestionForm()
    answer = None
    error = None

    # Load history from session (list of dicts)
    history = request.session.get('qa_history', [])

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.cleaned_data['question']
            try:
                answer = answer_stats_question(question)

                # Save to session history
                history_entry = {
                    'question': question,
                    'success': answer['success'],
                    'concept': answer.get('concept', ''),
                    'summary': (
                        answer.get('intuition', '')[:120] + '...'
                        if answer.get('intuition')
                        else answer.get('out_of_scope_message', '')[:120] + '...'
                    ),
                }
                history.insert(0, history_entry)       # newest first
                history = history[:MAX_HISTORY]        # keep only last 5
                request.session['qa_history'] = history
                request.session.modified = True

            except Exception as e:
                error = f"AI pipeline error: {str(e)}"

    return render(request, 'core/ask.html', {
        'form': form,
        'answer': answer,
        'error': error,
        'history': history,
    })


def recent_questions(request):
    """Show the last MAX_HISTORY questions from session."""
    history = request.session.get('qa_history', [])
    return render(request, 'core/recent_questions.html', {'history': history})


def clear_history(request):
    """POST-only view to clear session history."""
    if request.method == 'POST':
        request.session['qa_history'] = []
        request.session.modified = True
    from django.shortcuts import redirect
    return redirect('recent_questions')