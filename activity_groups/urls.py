from django.conf.urls import url, patterns

from activity_groups import views

urlpatterns = patterns('',
        url(r'^setup_activity_group/$', views.ActivityMembersManager.as_view(), name='setup_activity_group'),

        url(r'^get_activity_group_list/(?P<school_id>\w+)/$', views.ActivityGroupList.as_view(),
            name='get_activity_group_list'),

        url(r'^get_activity_group_members/(?P<group_id>\w+)/$', views.ActivityGroupMembersList.as_view(),
            name='get_activity_group_members')
    )