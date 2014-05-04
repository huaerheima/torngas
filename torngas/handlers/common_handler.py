#!/usr/bin/env python# -*- coding: utf-8 -*-import base64import hmacimport hashlibimport timeimport threadingimport reimport tornadofrom tornado.web import RequestHandler, HTTPErrorfrom urllib import unquotefrom tornado.escape import utf8from torngas.utils import lazyimportfrom torngas.mixin.handler_mixin import UncaughtExceptionMixinfrom tornado.ioloop import IOLoopsignals_module = lazyimport('torngas.dispatch')settings_module = lazyimport('torngas.helpers.settings_helper')class CommonHandler(RequestHandler):    def __init__(self, application, request, **kwargs):        self._is_threaded = False        self._is_torngas_finished = False        self.current_appname = kwargs.pop('current_appname', None)        super(CommonHandler, self).__init__(application, request, **kwargs)    def initialize(self, *args, **kwargs):        pass    def prepare(self):        if not self.application.middleware_manager.run_request_hooks(self):            self.on_prepare()    def on_prepare(self):        """        因为prepare被使用，提供此方法以供需要在prepare之后进行一些业务处理        """        pass    def reverse_url(self, name, *args):        url = super(CommonHandler, self).reverse_url(self.current_appname + '-' + name, *args)        if url.endswith('?'):            return url[:-1]        return url    def create_post_token(self):        """        返回一个当前时间戳的16进制哈希码，用来做post 请求的验证token        """        timestamp = utf8(str(int(time.time())))        value = base64.b64encode(utf8(timestamp))        hashtxt = hmac.new(utf8(value), digestmod=hashlib.sha1)        return utf8(hashtxt.hexdigest())    def finish(self, chunk=None):        self._is_torngas_finished = True        is_finished = self.application.middleware_manager.run_response_hooks(self)        if self._is_threaded:            self._chunk = chunk            IOLoop.instance().add_callback(self.threaded_finish_callback)            return        if not is_finished:            super(CommonHandler, self).finish(chunk)    def get_user_locale(self):        if settings_module.settings.TRANSLATIONS_CONF.use_accept_language:            return None        return tornado.locale.get(settings_module.settings.TRANSLATIONS_CONF.locale_default)    def cleanup_param(self, val, strip=True):        # Get rid of any weird control chars        value = re.sub(r"[\x00-\x08\x0e-\x1f]", " ", val)        value = tornado.web._unicode(value)        if strip: value = value.strip()        return unquote(value)    def threaded_finish_callback(self):        """        如果使用多线程回调装饰器，此方法将起作用        :return:        """        if self.application.settings.get('debug', False):            print "In the finish callback thread is ", str(threading.currentThread())        super(CommonHandler, self).finish(self._chunk)        self._chunk = None    def write(self, chunk, status=None):        if status:            self.set_status(status)        super(CommonHandler, self).write(chunk)class WebHandler(UncaughtExceptionMixin, CommonHandler):    def create_template_loader(self, template_path):        loader = self.application.tmpl        if loader is None:            return super(CommonHandler, self).create_template_loader(template_path)        else:            return loader(template_path)class ErrorHandler(UncaughtExceptionMixin, CommonHandler):    def prepare(self):        super(ErrorHandler, self).prepare()        self.set_status(404)        raise HTTPError(404)tornado.web.ErrorHandler = ErrorHandler