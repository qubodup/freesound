# -*- coding: utf-8 -*-

#
# Freesound is (c) MUSIC TECHNOLOGY GROUP, UNIVERSITAT POMPEU FABRA
#
# Freesound is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Freesound is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#     See AUTHORS file.
#

from django.http import HttpResponse
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
import follow.utils
from follow.models import FollowingUserItem
from follow.models import FollowingQueryItem
from django.contrib.auth.models import User
from django.shortcuts import redirect, render_to_response
from datetime import datetime, timedelta
from search.views import search_prepare_query, search_prepare_sort
import settings
from freesound.utils.search.solr import Solr, SolrResponseInterpreter
from search.forms import SEARCH_SORT_OPTIONS_WEB
# from utils.search.solr import Solr, SolrQuery, SolrException, SolrResponseInterpreter, SolrResponseInterpreterPaginator
try:
    from collections import OrderedDict
except:
    from freesound.utils.ordered_dict import OrderedDict
from django.core.urlresolvers import reverse

@login_required
def follow_user(request, username):
    # create following user item relation
    user_from = request.user
    user_to = User.objects.get(username=username)
    fui = FollowingUserItem(user_from=user_from, user_to=user_to)
    fui.save()
    return HttpResponse()

@login_required
def unfollow_user(request, username):
    user_from = request.user
    user_to = User.objects.get(username=username)
    FollowingUserItem.objects.get(user_from=user_from, user_to=user_to).delete()
    return HttpResponse()

@login_required
def follow_tags(request, slash_tags):
    user = request.user
    space_tags = slash_tags.replace("/", " ")
    FollowingQueryItem(user=user, query=space_tags).save()
    return HttpResponse()

@login_required
def unfollow_tags(request, slash_tags):
    user = request.user
    space_tags = slash_tags.replace("/", " ")
    FollowingQueryItem.objects.get(user=user, query=space_tags).delete()
    return HttpResponse()

@login_required
def stream(request):

    SELECT_OPTIONS = OrderedDict([
        ("last_week", "Last week"),
        ("last_month", "Last month"),
        ("specific_dates", "Specify dates...")
    ])

    SELECT_OPTIONS_DAYS = {
        "last_week": 7,
        "last_month": 30,
        "specific_dates": 0
    }

    user = request.user

    if request.method == "POST":
        select_value = request.POST.get("time_lapse")
        if select_value != "specific_dates":
            date_from = datetime.now() - timedelta(days=SELECT_OPTIONS_DAYS[select_value])
            date_to = datetime.now()
            time_lapse = follow.utils.build_time_lapse(date_from, date_to)
        else:
            date_from = request.POST.get("date_from")
            date_to = request.POST.get("date_to")
            time_lapse = "[%sT00:00:00Z TO %sT23:59:59.999Z]" % (date_from, date_to)

    # if first time going into the page, the default is last week
    else:
        date_from = datetime.now() - timedelta(days=SELECT_OPTIONS_DAYS["last_week"])
        date_to = datetime.now()
        time_lapse = follow.utils.build_time_lapse(date_from, date_to)

    users_sounds, tags_sounds = follow.utils.get_stream_sounds(user, time_lapse)

    return render_to_response('follow/stream.html', locals(), context_instance=RequestContext(request))