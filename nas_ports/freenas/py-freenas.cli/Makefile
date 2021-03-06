# $FreeBSD$

PORTNAME=	freenas.cli
PORTVERSION=	${PRODUCT_VERSION:C/\-.*//:C/\_.*//}
PORTREVISION=   ${REVISION}
PKGNAMEPREFIX=	${PYTHON_PKGNAMEPREFIX}

CATEGORIES=	freenas
VALID_CATEGORIES+= freenas

MAINTAINER=	dev@ixsystems.com
COMMENT=	FreeNAS Command Line Interface

BUILD_DEPENDS=	${PYTHON_PKGNAMEPREFIX}freenas.utils>0:${PORTSDIR}/freenas/py-freenas.utils \
		${PYTHON_PKGNAMEPREFIX}six>0:${PORTSDIR}/devel/py-six \
		${PYTHON_PKGNAMEPREFIX}ply>0:${PORTSDIR}/devel/py-ply

RUN_DEPENDS=	${PYTHON_PKGNAMEPREFIX}columnize>0:${PORTSDIR}/devel/py-columnize \
		${PYTHON_PKGNAMEPREFIX}natural>0:${PORTSDIR}/devel/py-natural \
		${PYTHON_PKGNAMEPREFIX}ply>0:${PORTSDIR}/devel/py-ply \
		${PYTHON_PKGNAMEPREFIX}termcolor>0:${PORTSDIR}/devel/py-termcolor \
		${PYTHON_PKGNAMEPREFIX}texttable>0:${PORTSDIR}/textproc/py-texttable \
		${PYTHON_PKGNAMEPREFIX}six>0:${PORTSDIR}/devel/py-six \
		${PYTHON_PKGNAMEPREFIX}pyte>0:${PORTSDIR}/devel/py-pyte \
		${PYTHON_PKGNAMEPREFIX}future>0:${PORTSDIR}/devel/py-future \
		${PYTHON_PKGNAMEPREFIX}freenas.utils>0:${PORTSDIR}/freenas/py-freenas.utils \
		${PYTHON_PKGNAMEPREFIX}freenas.dispatcher>0:${PORTSDIR}/freenas/py-freenas.dispatcher

USES=		python
USE_PYTHON=	autoplist distutils
EXTRACT_ONLY=

MAKE_ENV=	VERSION=${PRODUCT_VERSION}
WRKSRC=		/usr/middleware_src/cli

PLIST_FILES=	bin/cli bin/logincli

checksum fetch:
	${ECHO_CMD} ${.TARGET} not needed because building direct

post-install:
	${INSTALL_SCRIPT} ${WRKSRC}/tools/cli ${STAGEDIR}${PREFIX}/bin/
	${INSTALL_SCRIPT} ${WRKSRC}/tools/logincli ${STAGEDIR}${PREFIX}/bin/

.include <bsd.port.mk>
