# Create your views here.
# coding: UTF-8
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.views import generic

from polls.models import User

#
# 一覧表示
#
class IndexView(generic.ListView):
  template_name = 'polls/index.html'
  context_object_name = 'latest_poll_list'

  def get_queryset(self):
    # 最新のPollデータを５件取得
    return User.objects.order_by('-pub_date')[:5]

#
# 詳細表示
#
class DetailView(generic.DetailView):
    model = User
    template_name = 'polls/detail.html'

#
# 結果表示
#
class ResultsView(generic.DetailView):
    model = User
    template_name = 'polls/results.html'

#
# 投票
#  
def vote(request, poll_id):
  p = get_object_or_404(Poll, pk=poll_id)
  try:
    selected_choice = p.choice_set.get(pk=request.POST['choice'])
  except (KeyError, Choice.DoesNotExist):
    # Redisplay the poll voting form.
    return render(request, 'polls/detail.html', {
        'poll': p,
        'error_message': "You didn't select a choice.",
    })
  else:
    selected_choice.votes += 1
    selected_choice.save()
    # Always return an HttpResponseRedirect after successfully dealing
    # with POST data. This prevents data from being posted twice if a
    # user hits the Back button.
    return HttpResponseRedirect(reverse('results', args=(p.id,)))