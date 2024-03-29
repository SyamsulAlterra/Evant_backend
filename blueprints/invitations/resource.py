from flask import Blueprint
from flask_restful import Api, Resource, reqparse, marshal
from flask_jwt_extended import jwt_required, get_jwt_identity
from .model import Invitations
from blueprints.events.model import Events
from blueprints.users.model import Users
from blueprints import db, app

import json

bp_invitations = Blueprint('invitations', __name__)
api = Api(bp_invitations)

class InvitationsResource(Resource):

    """
    class for invitations resource
    """

    @jwt_required
    def get(self):

        """
        method to get all invitations 
        """
        identity = get_jwt_identity()
        user_id = int(identity['user_id'])

        invitations_query = Invitations.query.filter_by(invited_id=user_id, status=0).all()


        if invitations_query == []:
            return [], 200
        

        
        list_event_temporrary = []

        for event in invitations_query:
            event_new = marshal(event, Invitations.response_fields)
            event_id = event_new['event_id']


            '''take event object with that event is in user invited'''
            from_event_table = Events.query.get(event_id)
            from_event_table = marshal(from_event_table, Events.response_fields)
            
            '''take user object in creator condition'''
            creator = Users.query.get(from_event_table['creator_id'])
            creator = marshal(creator, Users.response_fields)
            
            '''take event category, duration, start, and endDate'''
            event_duration = from_event_table['duration']
            event_start = from_event_table['start_date']
            event_end = from_event_table['end_date']
            event_category = from_event_table['category']
            event_preference = from_event_table['preference']

            if event_preference is not None :
                continue

            response_fields_dummy = {
                'event_id' : from_event_table['event_id'],
                'event_name' : from_event_table['event_name'],
                'invited_id' : event_new['invited_id'],
                'creator_id' : creator['user_id'],
                'username_creator' : creator['username'],
                'status' : event_new['status'],
                'event_duration' : event_duration,
                'event_start' : event_start,
                'event_end' : event_end,
                'event_category' : event_category
            }
            list_event_temporrary.append(response_fields_dummy)
    
        return list_event_temporrary, 200, {'Content-Type':'application/json'}
    
    @jwt_required
    def post(self):

        """
        method to invite someone to an event
        """
        parser = reqparse.RequestParser()
        identity = get_jwt_identity()
        user_id = int(identity['user_id'])

        parser.add_argument('invited_id', location='json', required=True)
        invitation_data = parser.parse_args()

        '''
        Take all event id by creator_id
        '''
        events = Events.query.filter_by(creator_id = user_id)

        '''
        Take newest event_id
        '''
        event = events[-1]
        event = marshal(event, Events.response_fields)

        event_id = event['event_id']
        invited_id = invitation_data['invited_id']

        '''
        Add to init model
        '''
        invitation = Invitations(event_id, invited_id, 0)

        db.session.add(invitation)
        db.session.commit()

        return marshal(invitation, Invitations.response_fields), 200, {'Content-Type':'application/json'}
    
    @jwt_required
    def put(self, event_id):

        """
        method to accept invitation
        """
        identity = get_jwt_identity()
        user_id = int(identity['user_id'])

        invitations_query = Invitations.query.filter_by(event_id=event_id, invited_id=user_id, status=0).first()

        if invitations_query is None:
            return {'status':'NOT_FOUND'}, 404
        
        invitations_query.status = 1
        db.session.commit()

        return marshal(invitations_query, Invitations.response_fields), 200, {'Content-Type':'application/json'}

class InvitationsRejectResource(Resource):

    """
    class for reject invitations
    """

    @jwt_required
    def put(self, event_id):

        """
        method to reject invitation
        """
        identity = get_jwt_identity()
        user_id = int(identity['user_id'])

        invitations_query = Invitations.query.filter_by(event_id=event_id, invited_id=user_id).first()

        if invitations_query is None:
            return {'status':'NOT_FOUND'}, 404
        
        invitations_query.status = -1
        db.session.commit()

        return marshal(invitations_query, Invitations.response_fields), 200, {'Content-Type':'application/json'}

class DeclineEventResource(Resource):

    """
    class for user decline event, when the event have been generated
    """

    @jwt_required
    def delete(self, event_id):

        """
        when user decline for the event, then user invitation for that event will be deleted
        """
        user = get_jwt_identity()
        user_id = user['user_id']

        invitation_query = Invitations.query.filter_by(status = 1, invited_id = user_id).all()
        
        '''
        find invitation of user in specific event_id, then delete it
        '''
        if invitation_query == []:
            return {'status': 'NOT_FOUND'}, 404

        for invitation in invitation_query:
            invitation_new = marshal(invitation, Invitations.response_fields)
            if int(event_id) == invitation_new['event_id']:
                db.session.delete(invitation)
                db.session.commit()
                return {'status': 'DELETED'}, 200

# class GetResponseNotification(Resource):
#     """
#     class to collect event_id and event_name for notification
#     """
#     def get(self):
#         '''
#         get list of event_id and 
#         '''
#         user = get_jwt_identity()
#         user_id = user['user_id']

#         invitation_query = Invitations.query.filter_by(invited_id=user_id)
#         for 


 

api.add_resource(InvitationsResource, '', '/accept/<event_id>')
api.add_resource(InvitationsRejectResource, '/reject/<event_id>')
api.add_resource(DeclineEventResource, '/decline/<event_id>')
