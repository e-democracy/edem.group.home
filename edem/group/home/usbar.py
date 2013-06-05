# coding=utf-8
import random
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.component import createObject
from zope.contentprovider.interfaces import UpdateNotCalled
from gs.group.base import GroupContentProvider, GroupPage
from gs.group.base.interfaces import IGSGroupMarker
from gs.group.member.base import user_member_of_group
from gs.group.privacy.interfaces import IGSGroupVisibility
from gs.viewlet import SiteContentProvider, WeightOrderedViewletManager
from Products.CustomUserFolder.CustomUser import user_image_path
from Products.GSGroupMember.groupmembership import get_group_userids

USBARLIMIT = 5


class UsBar(GroupContentProvider):
    pageTemplateFileName = "browser/templates/usbar.pt"

    def __init__(self, group, request, view):
        global USBARLIMIT
        super(UsBar, self).__init__(group, request, view)
        self.__updated = False
        if self.referredBy == 'topic-us-bar':
            USBARLIMIT = 3

    @Lazy
    def userInfo(self):
        retval = self.loggedInUser
        return retval

    @property
    def referredBy(self):
        '''The value to be used for the rb parameter on links, indicating
        to analysts what and where the user clicked.'''
        page = ""
        parent = self.__parent__
        while isinstance(parent, SiteContentProvider)\
                or isinstance(parent, WeightOrderedViewletManager):
            parent = parent.__parent__
        if parent.__class__.__name__ == 'GSTopicView':
            # wbushey: I really wanted to do this check by isinstance, but
            # at the moment my head hurts too much to figure out
            # Products.Five.metaclass
            page = "topic-"
        elif isinstance(parent, GroupPage):
            # wbushey: Could be better. GroupPage != group home. But right now
            # the Us-bar is only displayed in two places.
            page = "grouphome-"
        return "%sus-bar" % page

    # TODO: Move.isMember to a base
    #   gs.group.member.viewlet.GroupMemberContentProvider class
    @Lazy
    def isMember(self):
        # --=mpj17=-- Cut 'n' paste software engineering from
        # gs.group.member.viewlet.member.GroupMemberViewlet
        retval = ((not self.loggedInUser.anonymous) and
                    user_member_of_group(self.loggedInUser, self.groupInfo))
        return retval

    @Lazy
    def vis(self):
        retval = IGSGroupVisibility(self.groupInfo)
        return retval

    @Lazy
    def isPrivate(self):
        ''' Indicates if the group the UsBar is being displayed in is
        Private'''
        return self.vis.isPrivate

    @Lazy
    def isPublic(self):
        ''' Indicates if the group the UsBar is being displayed in is Public'''
        return self.vis.isPublic

    def update(self):
        self.__updated = True

        self.usBarMembers = []
        if self.viewTopics:
            ctx = self.context
            site_root = ctx.site_root()

            # get_group_userids requires a group context
            while not IGSGroupMarker.providedBy(ctx) and ctx != site_root:
                ctx = ctx.aq_parent
            if not IGSGroupMarker.providedBy(ctx):
                raise LookupError('Group context can not be found.')

            ml = list(get_group_userids(ctx, ctx.getId()))
            random.shuffle(ml)

            for userId in ml:
                if user_image_path(ctx, userId):
                    user = createObject('groupserver.UserFromId', ctx,
                                    userId)
                    self.usBarMembers.append(user)
                if len(self.usBarMembers) >= USBARLIMIT:
                    break

    def render(self):
        if not self.__updated:
            raise UpdateNotCalled

        pageTemplate = ViewPageTemplateFile(self.pageTemplateFileName)
        return pageTemplate(self)
