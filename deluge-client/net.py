#!/usr/bin/python

"""
This example creates a multi-controller network from semi-scratch by
using the net.add*() API and manually starting the switches and controllers.

This is the "mid-level" API, which is an alternative to the "high-level"
Topo() API which supports parametrized topology classes.

Note that one could also create a custom switch class and pass it into
the Mininet() constructor.
"""

from mininet.net import Mininet
from mininet.node import Controller, OVSSwitch, RemoteController,CPULimitedHost
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.util import custom,pmonitor
from mininet.link import Intf
import commands
import threading
import time
import socket
import json

def multiControllerNet():
    "Create a network from semi-scratch with multiple controllers."

    NODE1_IP='192.168.144.126'
    NODE2_IP='192.168.144.134'
    CONTROLLER_IP='192.168.144.126'
    #net = Mininet( controller=Controller,host=CPULimitedHost)
    net = Mininet(controller=Controller)
    print "*** Creating (reference) controllers"
    c1 = net.addController( 'c1', port=6633 )
    #c1 = net.addController('c1', controller=RemoteController,ip='127.0.0.1',port=6633)
    #c2 = net.addController( 'c2', port=6634 )
    #c2 = net.addController('c2', controller=RemoteController,ip='127.0.0.1',port=6634)
    #c3 = net.addController( 'c3', port=6635 )
    #c3 = net.addController('c3', controller=RemoteController,ip='127.0.0.1',port=6635)

    layer = 3
    tmp = 1<<layer
    print "*** Creating switches"
    sdn_switch = [net.addSwitch('S%d'%(n)) for n in range(15,16)]
    left_switch = [net.addSwitch('L%d'%(n+1)) for n in range(tmp-1)]
    #right_switch = [net.addSwitch('R%d'%(n+tmp)) for n in range(tmp-1)]
    #f = open('switch_list','w')
    switch_name = [n.name for n in left_switch]
    #switch_name = switch_name + [n.name for n in right_switch]
    switch_name = switch_name + [n.name for n in sdn_switch]
    '''
    with open('switch_list','w') as f:
        f.write(' '.join(switch_name)) 
    print 'Finish writing switch_list'
    '''   
    print "*** Creating hosts"
    hosts1 = [ net.addHost( 'h%d' % (n+1) ,ip='10.0.0.%s'%(n+1)) for n in range(tmp) ]
    #hosts2 = [ net.addHost( 'h%d' % (n+1+tmp) ) for n in range(tmp) ]

    print "*** Creating links"
    for i in range(len(left_switch)/2):
        net.addLink(left_switch[i],left_switch[(i+1)*2-1])
        net.addLink(left_switch[i],left_switch[(i+1)*2])
    #for i in range(len(right_switch)/2):
    #    net.addLink(right_switch[i],right_switch[(i+1)*2-1])
    #    net.addLink(right_switch[i],right_switch[(i+1)*2])
    for i in range(len(sdn_switch)):
        #net.addLink(sdn_switch[i],right_switch[0])
        net.addLink(sdn_switch[i],left_switch[0])
    #net.addLink(sdn_switch[0],sdn_switch[1])
  
    ''' 
    for i in range(4): 
        for j in range(2):
            net.addLink(left_switch[i+3],hosts1[2*i+j])
            net.addLink(right_switch[i+3],hosts2[2*i+j])
    '''
    tmp >>= 1
    for i in range(tmp):
        for j in range(2):
            net.addLink(left_switch[i+tmp-1],hosts1[2*i+j])
            #net.addLink(right_switch[i+tmp-1],hosts2[2*i+j])

    print "*** Starting network"
    net.build()
    net.addNAT(ip='10.0.0.254').configDefault()
    #nat = net.addNAT(connect=None)
    #net.addLink(nat,sdn_switch[0])
    #nat.configDefault()
    #net.build()
    c1.start()
    #c2.start()
    #c3.start()
    for k in left_switch:
        k.start([c1])
    #for k in right_switch:
    #    k.start([c2])
    for k in sdn_switch:
        k.start([c1])
    
    sdn_switch[0].cmdPrint('ovs-vsctl add-port '+sdn_switch[0].name+' '+sdn_switch[0].name+'-gre1 -- set interface '+sdn_switch[0].name+'-gre1 type=gre options:remote_ip='+NODE2_IP)
    for k in hosts1:
        k.cmdPrint('ip link set mtu 1454 dev '+k.name+'-eth0')
    nat = net.get('nat0')
    nat.cmdPrint('ip link set mtu 1454 dev nat0-eth0')
    print "*** Testing network"
    #net.pingAll()
    out = {}
    popens = {}
    count = {}
    for i in range(tmp<<1):
        print 'activate',i
        #popens[hosts1[i]] = hosts1[i].popen('python client.py 1 1 %s user1 > %s &'%(i,'user1'+str(i)))
        popens[hosts1[i]] = hosts1[i].popen('python client.py 1 1 %s user1'%(i))
        #popens[hosts2[i]] = hosts2[i].popen('python client.py 1 2 %s user1 > %s &'%(i,'user2'+str(i)))
        #hosts1[i].cmdPrint('python client.py 1 1 %s user1 > %s &'%(i,'user1'+str(i)))
        #hosts2[i].cmd('python client.py 1 2 %s user1 > %s &'%(i,'user2'+str(i)))
        out[hosts1[i].name] = open('user1'+str(i),'w')
        count[hosts1[i].name] = 0
    
    for host,line in pmonitor(popens):
        if host:
            out[host.name].write(line.strip()+'\n')
            count[host.name] += 1
            print count
            #print "<%s>: %s" % ( host.name, line.strip() )
    
    '''
    print 'host1'
    hosts1[0].cmd('python client.py 1 1 1 user1 > a &')
    print 'host2'
    hosts1[1].cmd('python client.py 1 1 2 user1 > b &')
    print "*** Running CLI"
    '''
    CLI( net )
    print count
    print "*** Stopping network"
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )  # for CLI output
    multiControllerNet()
