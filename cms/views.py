# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from cms.forms import UserForm
from cms.models import User

def user_list(request, user_id=None):
	'''get user_list'''
	users = User.objects.all().order_by('id')
	return render_to_response('cms/user_list.html',  # 使用するテンプレート
                              {'users': users},       # テンプレートに渡すデータ
                              context_instance=RequestContext(request))  # その他標準のコンテキスト

def user_edit(request, user_id=None):
	'''add user'''
	if user_id:   # book_id が指定されている (修正時)
		user = get_object_or_404(User, pk=1)
		print user_id

	else:         # book_id が指定されていない (追加時)
		user = User()

	if request.method == 'POST':
		form = UserForm(request.POST, instance=user)  # POST された request データからフォームを作成
		if form.is_valid():    # フォームのバリデーション
			user = form.save(commit=False)
			user.save()
			return redirect('cms/user/')
	else:    # GET の時
		form = UserForm(instance=user)  # book インスタンスからフォームを作成

	return render_to_response('cms/user_edit.html',
                              dict(form=form, user_id=user_id),
                              context_instance=RequestContext(request))

def user_del(request, user_id):
	'''del user'''
	print user_id
	user = get_object_or_404(User, pk=user_id)
	user.delete()
	return redirect('cms/user/')
