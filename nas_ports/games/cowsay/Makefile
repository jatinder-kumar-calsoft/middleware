# Created by: Kris Kennaway <kris@FreeBSD.org>
# $FreeBSD$

PORTNAME=	cowsay
PORTVERSION=	3.03
PORTREVISION=	2
CATEGORIES=	games
MASTER_SITES=	http://pkgs.fedoraproject.org/repo/pkgs/cowsay/cowsay-3.03.tar.gz/b29169797359420dadb998079021a494/

MAINTAINER=	wxs@FreeBSD.org
COMMENT=	Configurable talking characters in ASCII art

USES=		perl5

NO_BUILD=	# defined

.if defined(MAINTAINER_MODE)
DISTFILES+=	${DISTNAME}${EXTRACT_SUFX}.sig
verify: fetch
	@${ECHO_MSG} "Checking ${DISTNAME}${EXTRACT_SUFX}"
	@gpg --verify ${DISTDIR}/${DISTNAME}${EXTRACT_SUFX}.sig 2>/dev/null || echo "Bad signature!"
	@${ECHO_MSG} "Done"
.endif

post-patch:
	@${REINPLACE_CMD} 's,usethisperl=.*,usethisperl=${PERL},' ${WRKSRC}/install.sh

do-install:
	cd ${WRKSRC}; ${SH} install.sh ${STAGEDIR}${PREFIX}
	@${SED} -i '' 's,${STAGEDIR},,' ${STAGEDIR}${PREFIX}/bin/cowsay
	@${INSTALL_DATA} ${FILESDIR}/box.cow ${STAGEDIR}${PREFIX}/share/cows
	@${INSTALL_DATA} ${FILESDIR}/jkh.cow ${STAGEDIR}${PREFIX}/share/cows
	@${INSTALL_DATA} ${FILESDIR}/tux-stab.cow ${STAGEDIR}${PREFIX}/share/cows

.include <bsd.port.mk>
