from multiprocessing import cpu_count
import os

port = os.environ.get('PORT')

# bind = '0.0.0.0:443'
bind = '0.0.0.0:{}'.format(port)
workers = 1  # cpu_count() * 2 + 1
daemon = False
threads = 1
preload_app = False
proc_name = 'ci-server'
worker_class = 'gthread'
# pidfile = '/application/instacar-back/pid.txt'
# logfile = '/application/instacar-back/services/backend/results.log'
# pythonpath = 'app_notifications'
loglevel = 'info'

# ssl config
# keyfile = '/app_notifications/example.key'
# certfile = '/app_notifications/api_instacarshare_com.crt'
# ca_certs = '/app_notifications/bundle.crt'
