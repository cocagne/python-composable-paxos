import sys
import itertools
import os.path
import pickle

#from twisted.trial import unittest
import unittest

this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append( os.path.dirname(this_dir) )

from composable_paxos import *


PID = ProposalID


class ShortAsserts (object):

    at = unittest.TestCase.assertTrue
    ae = unittest.TestCase.assertEquals

    def am(self, msg, mtype, **kwargs):
        self.ae(msg.__class__.__name__.lower(), mtype)
        for k,v in kwargs.iteritems():
            self.assertEquals(getattr(msg,k), v)



class ProposerTests (ShortAsserts, unittest.TestCase):


    def setUp(self):
        self.p = Proposer('A', 2)

    
    def al(self, value):
        if hasattr(self.p, 'leader'):
            self.assertEquals( self.p.leader, value )

    def num_promises(self):
        if hasattr(self.p, 'promises_received'):
            return len(self.p.promises_received) # python version


    def test_constructor(self):
        self.al( False )
        self.ae( self.p.network_uid, 'A' )
        self.ae( self.p.quorum_size,  2  )

        
    def test_propose_value_no_value_while_not_leader(self):
        self.ae( self.p.proposed_value, None )
        m = self.p.propose_value( 'foo' )
        self.ae( m, None )
        self.ae( self.p.proposed_value, 'foo' )


    def test_propose_value_no_value_while_leader(self):
        self.p.leader = True
        self.ae( self.p.proposed_value, None )
        m = self.p.propose_value( 'foo' )
        self.am(m, 'accept', from_uid='A', proposal_id=PID(0,'A'), proposal_value='foo')
        self.ae( self.p.proposed_value, 'foo' )

        
    def test_propose_value_with_previous_value(self):
        self.p.propose_value( 'foo' )
        m = self.p.propose_value( 'bar' )
        self.ae(m, None)
        self.ae( self.p.proposed_value, 'foo' )
        

    def test_prepare(self):
        m = self.p.prepare()
        self.am(m, 'prepare', proposal_id = PID(1,'A'))
        self.al( False )


    def test_prepare_two(self):
        m = self.p.prepare()
        self.am(m, 'prepare', proposal_id = PID(1,'A'))
        m = self.p.prepare()
        self.am(m, 'prepare', proposal_id = PID(2,'A'))


    def test_nacks_pre_leader(self):
        m = self.p.prepare()
        self.am(m, 'prepare', proposal_id = PID(1,'A'))

        self.p.leader = True
        
        m = self.p.receive( Nack('B', 'A', PID(1,'A'), PID(5,'B')) )
        self.ae( m, None )
        self.ae( self.p.leader, True )
        self.ae( self.p.proposal_id, PID(1,'A') )

        m = self.p.receive( Nack('B', 'A', PID(1,'A'), PID(5,'B')) )
        self.ae( m, None )
        self.ae( self.p.leader, True )
        self.ae( self.p.proposal_id, PID(1,'A') )

        m = self.p.receive( Nack('C', 'A', PID(1,'A'), PID(6,'B')) )
        self.ae( self.p.leader, False )
        self.ae( self.p.proposal_id, PID(7,'A') )

        self.am(m, 'prepare', proposal_id = PID(7,'A'))

        
    def test_prepare_with_promises_received(self):
        m = self.p.prepare()
        self.am(m, 'prepare', proposal_id = PID(1, 'A'))
        self.ae( self.num_promises(), 0 )
        self.p.receive(Promise('B', 'A', PID(1,'A'), None, None))
        self.ae( self.num_promises(), 1 )
        m = self.p.prepare()
        self.am(m, 'prepare', proposal_id = PID(2,'A'))
        self.ae( self.num_promises(), 0 )

        
    def test_recv_promise_ignore_other_nodes(self):
        self.p.prepare()
        self.ae( self.num_promises(), 0 )
        self.p.receive(Promise('B', 'B', PID(1,'B'), None, None ))
        self.ae( self.num_promises(), 0 )
    
        
    def test_recv_promise_ignore_duplicate_response(self):
        self.p.prepare()
        self.p.receive( Promise('B', 'A', PID(1,'A'), None, None ) )
        self.ae( self.num_promises(), 1 )
        self.p.receive( Promise('B', 'A', PID(1,'A'), None, None ) )
        self.ae( self.num_promises(), 1 )


    def test_recv_promise_propose_value_from_null(self):
        self.p.prepare()
        self.p.prepare()
        self.ae( self.p.highest_accepted_id, None )
        self.ae( self.p.proposed_value, None )
        self.p.receive( Promise('B', 'A', PID(2,'A'), PID(1,'B'), 'foo') )
        self.ae( self.p.highest_accepted_id, PID(1,'B') )
        self.ae( self.p.proposed_value, 'foo' )

        
    def test_recv_promise_override_previous_proposal_value(self):
        self.p.prepare()
        self.p.prepare()
        self.p.prepare()
        self.p.receive( Promise('B', 'A', PID(3,'A'), PID(1,'B'), 'foo') )
        m = self.p.prepare()
        self.am(m, 'prepare', proposal_id = PID(4,'A'))
        self.p.receive( Promise('B', 'A', PID(4,'A'), PID(3,'B'), 'bar') )
        self.ae( self.p.highest_accepted_id, PID(3,'B') )
        self.ae( self.p.proposed_value, 'bar' )

        
    def test_recv_promise_ignore_previous_proposal_value(self):
        self.p.prepare()
        self.p.prepare()
        self.p.prepare()
        self.p.receive( Promise('B', 'A', PID(3,'A'), PID(1,'B'), 'foo') )
        self.p.prepare()
        self.p.receive( Promise('B', 'A', PID(4,'A'), PID(3,'B'), 'bar') )
        self.ae( self.p.highest_accepted_id, PID(3,'B') )
        self.ae( self.p.proposed_value, 'bar' )
        self.p.receive( Promise('C', 'C', PID(4,'A'), PID(2,'B'), 'baz') )
        self.ae( self.p.highest_accepted_id, PID(3,'B') )
        self.ae( self.p.proposed_value, 'bar' )



        
class AcceptorTests (ShortAsserts, unittest.TestCase):

    acceptor_factory = None 

    def setUp(self):        
        self.a = Acceptor('A')


    def test_recv_prepare_initial(self):
        self.ae( self.a.promised_id    , None)
        self.ae( self.a.accepted_value , None)
        self.ae( self.a.accepted_id    , None)
        m = self.a.receive( Prepare('A', PID(1,'A')) )
        self.am(m, 'promise', proposer_uid='A', proposal_id=PID(1,'A'), last_accepted_id=None, last_accepted_value=None)

        
    def test_recv_prepare_duplicate(self):
        m = self.a.receive( Prepare('A', PID(1,'A')) )
        self.am(m, 'promise', proposer_uid='A', proposal_id=PID(1,'A'), last_accepted_id=None, last_accepted_value=None)
        m = self.a.receive( Prepare('A', PID(1,'A')) )
        self.am(m, 'promise', proposer_uid='A', proposal_id=PID(1,'A'), last_accepted_id=None, last_accepted_value=None)


    def test_recv_prepare_less_than_promised(self):
        m = self.a.receive( Prepare('A', PID(5,'A')) )
        self.am(m, 'promise', proposer_uid='A', proposal_id=PID(5,'A'), last_accepted_id=None, last_accepted_value=None)
        m = self.a.receive( Prepare('A', PID(1,'A')) )
        self.am(m, 'nack', proposal_id=PID(1,'A'), proposer_uid='A', promised_proposal_id=PID(5,'A'))

        
    def test_recv_prepare_override(self):
        m = self.a.receive( Prepare('A', PID(1,'A')) )
        self.am(m, 'promise', proposer_uid='A', proposal_id=PID(1,'A'), last_accepted_id=None, last_accepted_value=None)
        
        m = self.a.receive( Accept('A', PID(1,'A'), 'foo') )
        self.am(m, 'accepted', from_uid='A', proposal_id=PID(1,'A'), proposal_value='foo')

        m = self.a.receive( Prepare('B', PID(2,'B') ) )
        self.am(m, 'promise', proposer_uid='B', proposal_id=PID(2,'B'), last_accepted_id=PID(1,'A'), last_accepted_value='foo')


    def test_recv_accept_request_initial(self):
        m = self.a.receive( Accept('A', PID(1,'A'), 'foo') )
        self.am(m, 'accepted', proposal_id=PID(1,'A'), proposal_value='foo')

        
    def test_recv_accept_request_promised(self):
        m = self.a.receive( Prepare('A', PID(1,'A') ) )
        self.am(m, 'promise', proposer_uid='A', proposal_id=PID(1,'A'), last_accepted_id=None, last_accepted_value=None)
        
        m = self.a.receive( Accept('A', PID(1,'A'), 'foo') )
        self.am(m, 'accepted', proposal_id=PID(1,'A'), proposal_value='foo')

        
    def test_recv_accept_request_greater_than_promised(self):
        m = self.a.receive( Prepare('A', PID(1,'A') ) )
        self.am(m, 'promise', proposer_uid='A', proposal_id=PID(1,'A'), last_accepted_id=None, last_accepted_value=None)

        m = self.a.receive( Accept('A', PID(5,'A'), 'foo') )
        self.am(m, 'accepted', proposal_id=PID(5,'A'), proposal_value='foo')


    def test_recv_accept_request_less_than_promised(self):
        m = self.a.receive( Prepare('A', PID(5,'A') ) )
        self.am(m, 'promise', proposer_uid='A', proposal_id=PID(5,'A'), last_accepted_id=None, last_accepted_value=None)

        m = self.a.receive( Accept('A', PID(1,'A'), 'foo') )
        self.am(m, 'nack', proposal_id=PID(1,'A'), proposer_uid='A', promised_proposal_id=PID(5,'A'))
        
        self.ae( self.a.accepted_value, None )
        self.ae( self.a.accepted_id,    None )
        self.ae( self.a.promised_id,    PID(5,'A'))



class LearnerTests (ShortAsserts, unittest.TestCase):

    def setUp(self):        
        self.l = Learner('A', 2)

    def test_basic_resolution(self):
        self.ae( self.l.quorum_size, 2    )
        self.ae( self.l.final_value, None )

        self.l.receive( Accepted('A', PID(1,'A'), 'foo') )
        self.ae( self.l.final_value, None )
        m = self.l.receive( Accepted('B', PID(1,'A'), 'foo') )
        self.ae( self.l.final_value, 'foo' )

        self.am(m, 'resolution', from_uid='A', value='foo')
        self.ae(self.l.final_acceptors, set(['A', 'B']))


    def test_ignore_after_resolution(self):
        self.l.receive( Accepted('A', PID(1,'A'), 'foo') )
        self.ae( self.l.final_value, None )

        self.l.receive( Accepted('B', PID(1,'A'), 'foo') )
        self.ae( self.l.final_value, 'foo' )

        m = self.l.receive( Accepted('A', PID(5,'A'), 'bar') )
        self.am(m, 'resolution', from_uid='A', value='foo')
        
        m = self.l.receive( Accepted('B', PID(5,'A'), 'bar') )
        self.am(m, 'resolution', from_uid='A', value='foo')
        self.ae( self.l.final_value, 'foo' )
        self.ae(self.l.final_acceptors, set(['A', 'B']))
        

    def test_ignore_duplicate_messages(self):
        self.l.receive( Accepted('A', PID(1,'A'), 'foo') )
        self.ae( self.l.final_value, None )
        self.l.receive( Accepted('A', PID(1,'A'), 'foo') )
        self.ae( self.l.final_value, None )
        self.l.receive( Accepted('B', PID(1,'A'), 'foo') )
        self.ae( self.l.final_value, 'foo' )

        
    def test_ignore_old_messages(self):
        self.l.receive( Accepted('A', PID(5,'A'), 'foo') )
        self.ae( self.l.final_value, None )
        self.l.receive( Accepted('A', PID(1,'A'), 'bar') )
        self.ae( self.l.final_value, None )
        self.l.receive( Accepted('B', PID(5,'A'), 'foo') )
        self.ae( self.l.final_value, 'foo' )


    def test_resolve_with_mixed_proposal_versions(self):
        self.l.receive( Accepted('A', PID(5,'A'), 'foo') )
        self.ae( self.l.final_value, None )
        self.l.receive( Accepted('B', PID(1,'A'), 'foo') )
        self.ae( self.l.final_value, None )
        self.l.receive( Accepted('C', PID(1,'A'), 'foo') )
        self.ae( self.l.final_value, 'foo' )
        self.ae(self.l.final_acceptors, set(['B', 'C']))

        self.l.receive( Accepted('A', PID(5,'A'), 'foo') )
        self.ae(self.l.final_acceptors, set(['A', 'B', 'C']))


    def test_overwrite_old_messages(self):
        self.l.receive( Accepted('A', PID(1,'A'), 'bar') )
        self.ae( self.l.final_value, None )
        self.l.receive( Accepted('B', PID(5,'A'), 'foo') )
        self.ae( self.l.final_value, None )
        self.l.receive( Accepted('A', PID(5,'A'), 'foo') )
        self.ae( self.l.final_value, 'foo' )


class PaxosInstanceTester (ProposerTests, AcceptorTests, LearnerTests):

    def setUp(self):
        pla = PaxosInstance('A',2)
        self.p = pla
        self.a = pla
        self.l = pla


if __name__ == '__main__':
    unittest.main()
