from datetime import datetime, timedelta, date

from django.contrib import auth
from django.conf import settings
from django.template import RequestContext
from django.template import Context, loader
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseServerError, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone

from forms import *
from models import *

import arp
from staff.models import Member

@staff_member_required
def index(request):
	if request.method == 'POST':
		form = UploadFileForm(request.POST, request.FILES)
		if form.is_valid():
			file = request.FILES['file']
			# Check the upload logs to make sure we haven't already loaded this file
			if (UploadLog.objects.filter(file_name=file.name).count() > 0):
				raise Exception('File Already Loaded')
			if request.user.is_authenticated():
				UploadLog.objects.create(user=request.user, file_name=file.name, file_size=file.size)
			else:
				UploadLog.objects.create(file_name=file.name, file_size=file.size)
			arp.import_file(file)
			#return HttpResponseRedirect('/success/url/')
	else:
		 form = UploadFileForm()
	return render_to_response('arpwatch/index.html', {'form': form}, context_instance=RequestContext(request))

def import_files(request):
	page_message = "success"
	try:
	    arp.import_all()
	except RuntimeError as err:
	    page_message = err
		
	return render_to_response('arpwatch/import.html', {'page_message': page_message}, context_instance=RequestContext(request))

@staff_member_required
def device_list(request):
	devices = UserDevice.objects.filter(ignore=False)
	return render_to_response('arpwatch/device_list.html', {'devices': devices}, context_instance=RequestContext(request))

@staff_member_required
def device(request, id):
	device = UserDevice.objects.get(pk=id)
	logs = ArpLog.objects.for_device(id)
	return render_to_response('arpwatch/device_view.html', {'device': device, 'logs': logs}, context_instance=RequestContext(request))

@staff_member_required
def device_logs_today(request):
	# Kinda clunky but it works
	now = timezone.now()
	return device_logs_by_day(request, str(now.year), str(now.month), str(now.day));

@staff_member_required
def device_logs_by_day(request, year, month, day):
	if len(month) == 1: month = "0" + month
	log_date = date(year=int(year), month=int(month), day=int(day))
	day_start = datetime.strptime(year + month + day + " 00:00", "%Y%m%d %H:%M")
	day_end = datetime.strptime(year + month + day + " 23:59", "%Y%m%d %H:%M")
	device_logs = ArpLog.objects.for_range(day_start, day_end)	
	return render_to_response('arpwatch/device_logs.html', {'device_logs':device_logs, 'day': log_date, 'next_day':log_date + timedelta(days=1), 'previous_day':log_date - timedelta(days=1)}, context_instance=RequestContext(request))

@staff_member_required
def logins_today(request):
	now = timezone.now()
	return logins_by_day(request, str(now.year), str(now.month), str(now.day));

def logins_by_day(request, year, month, day):
	if len(month) == 1: month = "0" + month
	log_date = date(year=int(year), month=int(month), day=int(day))
	start = datetime.strptime(year + month + day + " 00:00", "%Y%m%d %H:%M")
	end = datetime.strptime(year + month + day + " 23:59", "%Y%m%d %H:%M")
	logs = UserRemoteAddr.objects.filter(logintime__gt=start, logintime__lt=end)
	return render_to_response('arpwatch/user_logins.html', {'logs':logs, 'day': log_date, 'next_day':log_date + timedelta(days=1), 'previous_day':log_date - timedelta(days=1)}, context_instance=RequestContext(request))

# Copyright 2011 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
