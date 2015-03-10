# -*- coding: utf-8 -*-

import os
import subprocess

from module.plugins.Hook import Hook
from module.utils import fs_encode, save_join


class ExternalScripts(Hook):
    __name__    = "ExternalScripts"
    __type__    = "hook"
    __version__ = "0.32"

    __config__ = [("activated", "bool", "Activated"         , True ),
                  ("waitend"  , "bool", "Wait script ending", False)]

    __description__ = """Run external scripts"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay"         , "mkaay@mkaay.de"   ),
                       ("RaNaN"         , "ranan@pyload.org" ),
                       ("spoob"         , "spoob@pyload.org" ),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    event_list = ["archive_extracted", "package_extracted", "all_archives_extracted", "all_archives_processed",
                  "allDownloadsFinished", "allDownloadsProcessed"]


    #@TODO: Remove in 0.4.10
    def initPeriodical(self):
        pass


    def setup(self):
        self.scripts = {}

        folders = ["download_preparing", "download_finished", "all_downloads_finished", "all_downloads_processed",
                   "before_reconnect", "after_reconnect",
                   "package_finished", "package_extracted",
                   "archive_extracted", "all_archives_extracted", "all_archives_processed",
                   # deprecated folders
                   "unrar_finished", "all_dls_finished", "all_dls_processed"]

        for folder in folders:
            self.scripts[folder] = []
            for dir in (pypath, ''):
                self.initPluginType(folder, os.path.join(dir, 'scripts', folder))

        for script_type, names in self.scripts.iteritems():
            if names:
                self.logInfo(_("Installed scripts for ") + script_type, ", ".join(map(os.path.basename, names)))


    def initPluginType(self, name, dir):
        if not os.path.isdir(dir):
            try:
                os.makedirs(dir)

            except IOError, e:
                self.logDebug(e)
                return

        for filename in os.listdir(dir):
            file = os.path.join(dir, filename)

            if not os.path.isfile(file):
                continue

            if filename[0] in ("#", "_") or filename.endswith("~") or filename.endswith(".swp"):
                continue

            if not os.access(file, os.X_OK):
                self.logWarning(_("Script not executable:") + " %s/%s" % (name, filename))

            self.scripts[name].append(file)


    def callScript(self, script, *args):
        try:
            cmd = [script] + [(str(x) if not isinstance(x, basestring) else x).encode('utf-8') for x in args]

            self.logDebug("Executing", os.path.abspath(script), " ".join(cmd))

            p = subprocess.Popen(cmd, bufsize=-1)  #@NOTE: output goes to pyload
            if self.getConfig('waitend'):
                p.communicate()

        except Exception, e:
            self.logError(_("Error in %(script)s: %(error)s") % {"script": os.path.basename(script), "error": e})


    def downloadPreparing(self, pyfile):
        for script in self.scripts['download_preparing']:
            self.callScript(script, pyfile.pluginname, pyfile.url, pyfile.id)


    def downloadFinished(self, pyfile):
        download_folder = self.config['general']['download_folder']
        for script in self.scripts['download_finished']:
            file = save_join(download_folder, pyfile.package().folder, pyfile.name)
            self.callScript(script, pyfile.pluginname, pyfile.url, pyfile.name, file, pyfile.id)


    def packageFinished(self, pypack):
        download_folder = self.config['general']['download_folder']
        for script in self.scripts['package_finished']:
            folder = save_join(download_folder, pypack.folder)
            self.callScript(script, pypack.name, folder, pypack.password, pypack.id)


    def beforeReconnecting(self, ip):
        for script in self.scripts['before_reconnect']:
            self.callScript(script, ip)


    def afterReconnecting(self, ip):
        for script in self.scripts['after_reconnect']:
            self.callScript(script, ip)


    def archive_extracted(self, pyfile, folder, filename, files):
        for script in self.scripts['archive_extracted']:
            self.callScript(script, folder, filename, files)
        for script in self.scripts['unrar_finished']:  #: deprecated
            self.callScript(script, folder, filename)


    def package_extracted(self, pypack):
        download_folder = self.config['general']['download_folder']
        for script in self.scripts['package_extracted']:
            folder = save_join(download_folder, pypack.folder)
            self.callScript(script, pypack.name, folder, pypack.password, pypack.id)


    def all_archives_extracted(self):
        for script in self.scripts['all_archives_extracted']:
            self.callScript(script)


    def all_archives_processed(self):
        for script in self.scripts['all_archives_processed']:
            self.callScript(script)


    def allDownloadsFinished(self):
        for script in self.scripts['all_downloads_finished'] + self.scripts['all_dls_finished']:
            self.callScript(script)


    def allDownloadsProcessed(self):
        for script in self.scripts['all_downloads_processed'] + self.scripts['all_dls_processed']:
            self.callScript(script)
