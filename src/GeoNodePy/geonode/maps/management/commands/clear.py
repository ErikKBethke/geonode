import os
import shutil
from django.core.management.base import CommandError, NoArgsCommand
from geonode.maps.management.commands.stop import kill_geonode

class Command(NoArgsCommand):
    can_import_settings = True

    def handle_noargs(self, **options):

        from django.conf import settings
        PROJECT_HOME = os.path.join(settings.PROJECT_ROOT, '..', '..')
        geoserver = os.path.join(PROJECT_HOME, 'tomcat', 'webapps', 'geoserver-geonode-dev')
        geonetwork = os.path.join(PROJECT_HOME, 'tomcat', 'webapps', 'geonetwork')
        if settings.DEBUG:
            print "Stopping GeoNode"
            kill_geonode()
            print "Removing GeoServer and Geonetwork dirs"
            if os.path.exists(geoserver):
                shutil.rmtree(geoserver)
            if os.path.exists(geonetwork):
                shutil.rmtree(geonetwork)
        else:
            print "This command only works in DEBUG mode to prevent you from losing data"
