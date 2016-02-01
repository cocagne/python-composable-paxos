# python-composable-paxos

This repository implements the core Paxos algorithm as a set of composable
Python classes. 

In order to use this module properly, a basic understanding of Paxos is
required. The algorithm requires adherence to several messaging rules and that
state be saved to persistent media at certain points in the protocol. These
classes rely on the enclosing application to supply that behavior and to provide
solutions for the implementation-defined aspects of the protocol such as the
mechanism to ensure forward progress. The [Understanding
Paxos](https://understandingpaxos.wordpress.com/) paper provides a comprehensive
overview of the Paxos algorithm and should provide sufficient context for using
this module appropriately.

The advantage to this minimalist approach over more full-featured solutions is
flexibility. These classes have no external dependencies and they make no
assumptions about the application's operational environment or message handling
semantics. All they do is correctly implement the core algorithm in a neat
little black box that can be used as a foundational building block for
distributed applications.

This module may be installed via "pip install composable-paxos"

