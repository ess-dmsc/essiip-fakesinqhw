#!/usr/bin/env python
# vim: ft=python ts=8 sts=4 sw=4 expandtab autoindent smartindent nocindent
# author: Douglas Clowes (douglas.clowes@ansto.gov.au) 2014
# Connect to each instrument and get the DEPLOYMENT.TXT contents and "SICServer -v" response.
import os
import subprocess
import shlex
import traceback
import git

hosts = []
hosts += ["bilby"]
hosts += ["dingo"]
hosts += ["echidna"]
hosts += ["kookaburra"]
hosts += ["kowari"]
#hosts += ["lyrebird"]
hosts += ["pelican"]
hosts += ["platypus"]
hosts += ["quokka"]
hosts += ["taipan"]
hosts += ["wombat"]


class Instrument(object):

    def __init__(self, fqdn, txt):
        self.host = fqdn
        try:
            self.deployed_date = txt[0][6:16]
            self.built_date = txt[4][0:10]
            self.deployed_branch = txt[2].split()[2]
            self.deployed_hash = txt[2].split()[3]
            self.built_branch = txt[3].split()[1].split("=")[1]
            self.built_hash = txt[3].split()[2].split("=")[1]
            self.deployed_refs = []
            self.built_refs = []
            self.full_deployed_hash = None
            self.full_built_hash = None
            try:
                self.full_deployed_hash = repo.commit(self.deployed_hash.split('+')[0]).hexsha
                for ref in repo.refs:
                    if ref.commit.hexsha == self.full_deployed_hash:
                        self.deployed_refs.append(ref)
            except:
                pass
            try:
                self.full_built_hash = repo.commit(self.built_hash.split('+')[0]).hexsha
                for ref in repo.refs:
                    if ref.commit.hexsha == self.full_built_hash:
                        self.built_refs.append(ref)
            except:
                pass

        except Exception, err:
            print traceback.format_exc()
            print err

    def display(self):
        global Verbose
        print "Host:", self.host
        if self.deployed_date != self.built_date:
            print "**  Date:", self.deployed_date, self.built_date
        else:
            print "    Date:", self.deployed_date
        if self.deployed_branch != self.built_branch:
            print "**  Branch:", self.deployed_branch, self.built_branch
        else:
            print "    Branch:", self.deployed_branch
        if self.deployed_hash != self.built_hash:
            print "**  Hash:", self.deployed_hash,
            if len(self.deployed_refs):
                print "(", ", ".join([ref.name for ref in self.deployed_refs]), ")",
            elif self.full_deployed_hash is not None:
                print "(", self.full_deployed_hash, ")",
            print self.built_hash,
            if len(self.built_refs) > 0:
                print "(", ", ".join([ref.name for ref in self.built_refs]), ")",
            elif self.full_built_hash is not None:
                print "(", self.full_built_hash, ")",
            print
        else:
            print "    Hash:", self.deployed_hash,
            if len(self.deployed_refs) > 0:
                print "(", ", ".join([ref.name for ref in self.deployed_refs]), ")",
            print
        if Verbose:
            print "    Built:", self.full_built_hash, self.built_refs
            print "    Depld:", self.full_deployed_hash, self.deployed_refs

def do_one_host(host):
    global instrument_list
    global cmd_list
    global Verbose
    print "Host:", host
    if host in ["ics2-platypus"]:
        return
    host_fqdn = host + ".nbi.ansto.gov.au"

    cmd = "host " + host_fqdn
    txt, err = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    txt = txt.splitlines()
    err = err.splitlines()
    if Verbose:
        for line in txt:
            print "  Txt: %s" % line
        for line in err:
            print "  Err: %s" % line

    user = os.getlogin()
    cmd = "ssh -i /home/%s/.ssh/id_rsa %s" % (user, user)
    cmd += "@%s \"%s\"" % (host_fqdn, ";".join(cmd_list))
    if Verbose:
        print "  Cmd: %s" % cmd
    txt, err = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    txt = txt.splitlines()
    err = err.splitlines()
    if Verbose:
        for line in txt:
            print "  Txt: %s" % line
        for line in err:
            print "  Err: %s" % line
    if len(err) > 0:
        if not Verbose:
            for line in err:
                print "  Err: %s" % line
        return
    try:
        inst = Instrument(host_fqdn, txt)
        instrument_list.append(inst)
    except Exception, err:
        print traceback.format_exc()
        print err


def main_program():
    global instrument_list
    global cmd_list
    global repo
    global Verbose
    import argparse
    instrument_list = []
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--buildorder", action="store_true", help="list in build order")
    parser.add_argument("-n", "--newserver", action="store_true", help="use newserver instead of server")
    parser.add_argument("-t", "--test", action="store_true", help="add -test to host")
    parser.add_argument("-v", "--verbose", action="store_true", help="more output")
    parser.add_argument("-d", "--directory", default="server", help="use directory instead of server [server]")
    parser.add_argument("targets", nargs="*", help="select host target")
    args = parser.parse_args()
    Test = False
    if args.test:
        Test = True
    Verbose = False
    if args.verbose:
        Verbose = True
        print "Args:", args
    if args.newserver:
        cmd_list = []
        cmd_list += ["cat /usr/local/sics/newserver/DEPLOYMENT.TXT"]
        cmd_list += ["/usr/local/sics/newserver/SICServer -v"]
        cmd_list += ["stat --printf=%y" + "\\" * 4 + "n /usr/local/sics/newserver/SICServer"]
    else:
        cmd_list = []
        cmd_list += ["cat /usr/local/sics/%s/DEPLOYMENT.TXT" % args.directory]
        cmd_list += ["/usr/local/sics/%s/SICServer -v" % args.directory]
        cmd_list += ["stat --printf=%y" + ("\\" * 4 + "n") + (" /usr/local/sics/%s/SICServer" % args.directory)]

    repo = git.Repo()
    if len(args.targets) > 0:
        selected_hosts = []
        for target in args.targets:
            new_hosts = [h for h in hosts if h.startswith(target)]
            selected_hosts += new_hosts
    else:
        selected_hosts = [h for h in hosts]
    if Verbose:
        print "Selected Hosts:", selected_hosts
    for host in sorted(selected_hosts):
        if Test:
            host += "-test"
        for pre in ['ics1']:
            do_one_host('-'.join([pre, host]))
    if args.buildorder:
        for inst in sorted(instrument_list, key = lambda x: x.built_date):
            inst.display()
    else:
        for inst in sorted(instrument_list, key = lambda x: x.deployed_date):
            inst.display()

if __name__ == "__main__":
    main_program()
