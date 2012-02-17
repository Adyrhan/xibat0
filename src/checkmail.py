#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os, gtk
import pynotify, time
import threading, subprocess
import aescrypt
import feedparser, urllib2 as URL
from urllib2 import HTTPError, URLError

class EmailNotification(threading.Thread):
    def __init__(self, entry, nentry, nentries):
        threading.Thread.__init__(self)
        self.entry = entry
        self.nentry = nentry
        self.nentries = nentries
    
    def run(self):
        n = pynotify.Notification("Xibat0 Mail", "Mensaje "+str(self.nentry+1)+" de "+str(self.nentries)+"\n"+ \
                                                        "Autor: "+self.entry.author+"\n"+ \
                                                        "Asunto: "+self.entry.title)
        n.add_action("abrir", "Abrir mensaje", self.open_email)
        n.add_action("default", "Default Action", self.destroy)
        n.connect('closed', self.destroy)
        n.show()
        gtk.main()
        
    
    def open_email(self, n, action):
        print "Se ha clickeado en Abrir mensaje"
        subprocess.Popen(["gnome-open",self.entry.link])

    def destroy(self, n, action=None):
        print "Se ha cerrado el hilo"


class CheckMail():
    def __init__(self):
        gtk.gdk.threads_init()
        self.usr = ""
        self.passwd = ""
        self.fp = ""
        self.idcache = list()

        #First checks
        if pynotify.init("Xibat0 Mail"):
            n = pynotify.Notification("Xibat0 Mail", 
                                      "El servicio Xibat0 Mail ha sido iniciado.")
            n.show()
        else:
            print "Ha habido un problema al inicializar la libreria pynotify."
            sys.exit()
        self.mainloop()

    def get_feed(self):
        auth = URL.HTTPBasicAuthHandler()
        auth.add_password(
                realm='New mail feed',
                uri='https://mail.google.com',
                user='%s'%self.usr,
                passwd=self.passwd
                )
        opener = URL.build_opener(auth)
        URL.install_opener(opener)
        print("Se procede a autentificarse con "+self.usr+" y "+self.passwd)
        try:
            feed= URL.urlopen('https://mail.google.com/mail/feed/atom')
            return feed.read()
        except HTTPError, e:
            if e.code == 401:
                print "Autorización fallida: Nombre y/o contraseña incorrectos."
                n = pynotify.Notification("Xibat0 Mail", 
                                      "Nombre de usuario o contraseña incorrectos.")
                n.show()
                return "badcredentials"            
            else:
                raise e 

    def mainloop(self):
        while 1==1:
            feed = ""
            cfile = ""
            while self.usr == "" or self.passwd == "" or feed == "badcredentials":
                if feed == "badcredentials":
                    proc = subprocess.Popen("zenity --entry --text='Nombre de la cuenta'", stdout=subprocess.PIPE, shell=True)
                    proc.wait()
                    self.usr = proc.communicate()[0]
                    proc = subprocess.Popen("zenity --password --text='Contraseña'", stdout=subprocess.PIPE, shell=True)
                    proc.wait()
                    self.passwd = proc.communicate()[0]
                    #encrypt it using id command output
                    f1 = file(".xibato", "w")
                    f1.write(self.usr)
                    f1.write(self.passwd)
                    f1.close()
                    #save encripted data in ~/.xibato
                    
                #open credentials file
                try:
                    cfile = file(".xibato", "r")
                except IOError, e:
                    print "No existia el fichero, se creara una fichero nuevo"
                    feed="badcredentials"
                    continue
                 
                #decrypt credentials file
                #read credentials file and set usr and passwd
                self.usr = cfile.readline().strip('\n')
                print "Se ha leido del archivo el usuario: "+self.usr
                self.passwd = cfile.readline().strip('\n')
                print "Se ha leido del archivo el pass: "+self.passwd
                cfile.close()
                feed = self.get_feed()
            
            #usr and passwd no longer needed. removing data from ram.
            self.usr = ""
            self.passwd = ""
            self.fp = feedparser.parse(feed)
            if int(self.fp.feed.fullcount) == 0:
                continue
            i = 0
            idlist = list()
            print "Notificando mensajes"
            for entry in self.fp.entries:
                idlist.append(entry.id)
                if self.idcache.count(entry.id) == 0:
                    print "Notificando mensaje con id: "+str(entry.id)
                    self.idcache.append(entry.id)
                    e = EmailNotification(entry, i, self.fp.feed.fullcount)
                    e.start()
                    i = i + 1
            
            print "Eliminando caché de ids"
            for entryid in self.idcache:
                if idlist.count(entryid) == 0:
                    print "Eliminando id: "+entryid+" de la caché"
                    self.idcache.remove(entryid)
                    
            time.sleep(60)
        #aqui nunca llega...
        print "Se ha cerrado el main loop gtk"
        gtk.main_quit()
        sys.exit()

checkmail = CheckMail()

