PREFIX ?= /usr/local
PYTHON ?= python
BROWSERIFY_BUNDLE= ${PREFIX}/share/js-freenas-dispatcher/middleware.js

install:
	install etc/dispatcher ${STAGEDIR}${PREFIX}/etc/rc.d/
	install etc/middleware.conf ${STAGEDIR}${PREFIX}/etc/middleware.conf
	install tools/dispatcherd ${STAGEDIR}${PREFIX}/sbin/
	install tools/dispatcherctl ${STAGEDIR}${PREFIX}/sbin/
	install tools/sdsinit ${STAGEDIR}${PREFIX}/sbin/
	install tools/taskworker ${STAGEDIR}${PREFIX}/libexec/
	install -d ${STAGEDIR}${PREFIX}/lib/dispatcher/src
	install -d ${STAGEDIR}${PREFIX}/lib/dispatcher/plugins
	install -d ${STAGEDIR}${PREFIX}/lib/dispatcher/pydev
	install -d ${STAGEDIR}${PREFIX}/libexec/dispatcher
	cp -R src/ ${STAGEDIR}${PREFIX}/lib/dispatcher/src/
	cp -R plugins/ ${STAGEDIR}${PREFIX}/lib/dispatcher/plugins/
	cp -R pydev/ ${STAGEDIR}${PREFIX}/lib/dispatcher/pydev/
	cp -R libexec/ ${STAGEDIR}${PREFIX}/libexec/dispatcher/
	${PYTHON} setup.py install --install-lib=${STAGEDIR}${PREFIX}/lib/dispatcher/src/lib/
	${PYTHON} setup_plugins.py install --install-lib=${STAGEDIR}${PREFIX}/lib/dispatcher/plugins/
	cp ${BROWSERIFY_BUNDLE} ${STAGEDIR}${PREFIX}/lib/dispatcher/src/frontend/static/middleware.js
