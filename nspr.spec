%global nspr_version 4.32.0

# The upstream omits the trailing ".0", while we need it for
# consistency with the pkg-config version:
# https://bugzilla.redhat.com/show_bug.cgi?id=1578106
%{lua:
rpm.define(string.format("nspr_archive_version %s",
           string.gsub(rpm.expand("%nspr_version"), "(.*)%.0$", "%1")))
}

Summary:        Netscape Portable Runtime
Name:           nspr
Version:        %{nspr_version}
Release:        1%{?dist}
License:        MPLv2.0
URL:            http://ftp.mozilla.org/pub/nspr/releases/v${nspr_archive_version}/src
Group:          System Environment/Libraries
Conflicts:      filesystem < 3
BuildRequires:  gcc

# Sources available at ftp://ftp.mozilla.org/pub/mozilla.org/nspr/releases/
# When hg tag based snapshots are being used, refer to hg documentation on
# mozilla.org and check out subdirectory mozilla/nsprpub.
Source0:        %{name}-%{nspr_archive_version}.tar.gz
Source1:        nspr-config.xml

Patch1:         nspr-config-pc.patch
Patch2:         nspr-gcc-atomics.patch

%description
NSPR provides platform independence for non-GUI operating system 
facilities. These facilities include threads, thread synchronization, 
normal file and network I/O, interval timing and calendar time, basic 
memory management (malloc and free) and shared library linking.

%package devel
Summary:        Development libraries for the Netscape Portable Runtime
Group:          Development/Libraries
Requires:       nspr = %{version}-%{release}
Requires:       pkgconfig
BuildRequires:  xmlto
Conflicts:      filesystem < 3

%description devel
Header files for doing development with the Netscape Portable Runtime.

%prep

%setup -q -n %{name}-%{nspr_archive_version}

# Original nspr-config is not suitable for our distribution,
# because on different platforms it contains different dynamic content.
# Therefore we produce an adjusted copy of nspr-config that will be 
# identical on all platforms.
# However, we need to use original nspr-config to produce some variables
# that go into nspr.pc for pkg-config.

cp ./nspr/config/nspr-config.in ./nspr/config/nspr-config-pc.in
%patch1 -p0 -b .flags
pushd nspr
%patch2 -p1 -b .gcc-atomics
popd

%build
%define _configure ./nspr/configure
%configure \
                 --prefix=%{_prefix} \
                 --libdir=%{_libdir} \
                 --includedir=%{_includedir}/nspr4 \
%ifnarch noarch
%if 0%{__isa_bits} == 64
                 --enable-64bit \
%endif
%endif
%ifarch armv7l armv7hl armv7nhl
                 --enable-thumb2 \
%endif
                 --enable-optimize="$RPM_OPT_FLAGS" \
                 --disable-debug

# The assembly files are only for legacy atomics, to which we prefer GCC atomics
%ifarch i686 x86_64
sed -i '/^PR_MD_ASFILES/d' config/autoconf.mk
%endif
make

date +"%e %B %Y" | tr -d '\n' > date.xml
echo -n %{version} > version.xml

for m in %{SOURCE1}; do
  cp ${m} .
done
for m in nspr-config.xml; do
  xmlto man ${m}
done

%check

# Run test suite.
perl ./nspr/pr/tests/runtests.pl 2>&1 | tee output.log

TEST_FAILURES=`grep -c FAILED ./output.log` || :
if [ $TEST_FAILURES -ne 0 ]; then
  echo "error: test suite returned failure(s)"
  exit 1
fi
echo "test suite completed"

%install

%{__rm} -Rf $RPM_BUILD_ROOT

DESTDIR=$RPM_BUILD_ROOT \
  make install

mkdir -p $RPM_BUILD_ROOT%{_mandir}/man1 

NSPR_LIBS=`./config/nspr-config --libs`
NSPR_CFLAGS=`./config/nspr-config --cflags`
NSPR_VERSION=`./config/nspr-config --version`
%{__mkdir_p} $RPM_BUILD_ROOT/%{_libdir}/pkgconfig

# Get rid of the things we don't want installed (per upstream)
%{__rm} -rf \
   $RPM_BUILD_ROOT/%{_bindir}/compile-et.pl \
   $RPM_BUILD_ROOT/%{_bindir}/prerr.properties \
   $RPM_BUILD_ROOT/%{_libdir}/libnspr4.a \
   $RPM_BUILD_ROOT/%{_libdir}/libplc4.a \
   $RPM_BUILD_ROOT/%{_libdir}/libplds4.a \
   $RPM_BUILD_ROOT/%{_datadir}/aclocal/nspr.m4 \
   $RPM_BUILD_ROOT/%{_includedir}/nspr4/md

for f in nspr-config; do 
   install -c -m 644 ${f}.1 $RPM_BUILD_ROOT%{_mandir}/man1/${f}.1
done

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files
%{!?_licensedir:%global license %%doc}
%license nspr/LICENSE
%{_libdir}/libnspr4.so
%{_libdir}/libplc4.so
%{_libdir}/libplds4.so

%files devel
%{_includedir}/nspr4
%{_libdir}/pkgconfig/nspr.pc
%{_bindir}/nspr-config
%{_mandir}/man*/*

%changelog
* Thu Jun 17 2021 Bob Relyea <rrelyea@redhat.com> - 4.32.0-1
- Update to NSPR 4.32

* Thu Jun 17 2021 Bob Relyea <rrelyea@redhat.com> - 4.31.0-1
- Update to NSPR 4.31

* Tue Jun 1 2021 Bob Relyea <rrelyea@redhat.com> - 4.30.0-1
- Update to NSPR 4.30

* Mon Jun 29 2020 Daiki Ueno <dueno@redhat.com> - 4.25.0-2
- Rebuild

* Fri Jun  5 2020 Daiki Ueno <dueno@redhat.com> - 4.25.0-1
- Update to NSPR 4.25

* Fri May 24 2019 Daiki Ueno <dueno@redhat.com> - 4.21.0-2
- Rebuild

* Fri May 24 2019 Daiki Ueno <dueno@redhat.com> - 4.21.0-1
- Update to NSPR 4.21

* Wed Oct  3 2018 Daiki Ueno <dueno@redhat.com> - 4.20.0-2
- Prefer GCC atomics on i686 and x86_64

* Mon Sep  3 2018 Daiki Ueno <dueno@redhat.com> - 4.20.0-1
- Update to NSPR 4.20
- Use the upstream tarball as it is (rhbz#1578106)

* Thu Mar  8 2018 Daiki Ueno <dueno@redhat.com> - 4.19.0-1
- Update to NSPR 4.19
- Add gcc to BuildRequires

* Sat Feb 24 2018 Florian Weimer <fweimer@redhat.com> - 4.18.0-4
- Use LDFLAGS from redhat-rpm-config

* Thu Feb 08 2018 Fedora Release Engineering <releng@fedoraproject.org> - 4.18.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Tue Jan 30 2018 Daiki Ueno <dueno@redhat.com> - 4.18.0-2
- Rebuild

* Mon Jan 22 2018 Daiki Ueno <dueno@redhat.com> - 4.18.0-1
- Update to NSPR 4.18

* Wed Sep 20 2017 Daiki Ueno <dueno@redhat.com> - 4.17.0-1
- Update to NSPR 4.17

* Thu Aug  3 2017 Daiki Ueno <dueno@redhat.com> - 4.16.0-1
- Update to NSPR 4.16

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 4.15.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 4.15.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Wed Jun 21 2017 Daiki Ueno <dueno@redhat.com> - 4.15.0-1
- Update to NSPR 4.15

* Fri Apr 21 2017 Daiki Ueno <dueno@redhat.com> - 4.14.0-2
- Rebase to NSPR 4.14

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 4.13.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Fri Oct 21 2016 Daiki Ueno <dueno@redhat.com> - 4.13.1-1
- Rebase to NSPR 4.13.1

* Thu Sep 29 2016 Daiki Ueno <dueno@redhat.com> - 4.13.0-1
- Rebase to NSPR 4.13

* Sun Feb 21 2016 Elio Maldonado <emaldona@redhat.com> - 4.12.0-1
- Rebase to NSPR 4.12

* Mon Jan 18 2016 Elio Maldonado <emaldona@redhat.com> - 4.11.0-1
- Rebase to NSPR 4.11

* Sat Nov 14 2015 Elio Maldonado <emaldona@redhat.com> - 4.10.10-2
- Use __isa_bits macro instead of list of 64-bit architectures
- Patch contributed by Marcin Juszkiewicz <mjuszkiewicz@redhat.com>
- Resolves: Bug 1258425

* Thu Oct 29 2015 Elio Maldonado <emaldona@redhat.com> - 4.10.10-1
- Update to NSPR_4_10_10_RTM

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 4.10.8-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Thu Jan 29 2015 Elio Maldonado <emaldona@redhat.com> - 4.10.8-1
- Update to NSPR_4_10_8_RTM

* Tue Aug 19 2014 Elio Maldonado <emaldona@redhat.com> - 4.10.7-1
- Update to NSPR_4_10_7_RTM

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 4.10.6-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Fri Jul 18 2014 Tom Callaway <spot@fedoraproject.org> - 4.10.6-2
- fix license handling

* Tue Jun 10 2014 Elio Maldonado <emaldona@redhat.com> - 4.10.6-1
- Update to NSPR_4_10_6_RTM

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 4.10.5-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Tue May 06 2014 Elio Maldonado <emaldona@redhat.com> - 4.10.5-1
- Update to NSPR_4_10_5_RTM
- Remove patch no longer needed due to the rebase

* Wed Apr 02 2014 Elio Maldonado <emaldona@redhat.com> - 4.10.4-2
- Resolves: Bug 1083725 - Add ppc64le support to nspr
- Use a patch by Ulrich Weigand already applied upstream

* Sat Mar 15 2014 Elio Maldonado <emaldona@redhat.com> - 4.10.4-1
- Update to NSPR_4_10_4_RTM

* Thu Dec 05 2013 Dennis Gilmore <dennis@ausil.us> - 4.10.2-3
- escape the rpm macro in the previous commit

* Tue Dec  3 2013 Peter Robinson <pbrobinson@fedoraproject.org> 4.10.2-2
- Fix running %%configure to ensure appropriate config options and fix aarch64 builds

* Sat Nov 23 2013 Elio Maldonado <emaldona@redhat.com> - 4.10.2-1
- Update to NSPR_4_10_2_RTM
- Avoid unsigned integer wrapping in PL_ArenaAllocate
- Resolves: rhbz#1031465 - CVE-2013-5607

* Thu Sep 26 2013 Elio Maldonado <emaldona@redhat.com> - 4.10.1-1
- Update to NSPR_4_10_1_RTM

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 4.10.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Thu Jun 27 2013 Elio Maldonado <emaldona@redhat.com> - 4.10.0-3
- Repackage the source tar ball as nspr-4.10.0.tar.bz2
- Ensure client packages dependency resolution succeeds

* Tue Jun 18 2013 Elio Maldonado <emaldona@redhat.com> - 4.10-2
- Install man page for the nspr-config script

* Wed May 29 2013 Elio Maldonado <emaldona@redhat.com> - 4.10-1
- Update to NSPR_4_10_RTM

* Mon May 06 2013 Elio Maldonado <emaldona@redhat.com> - 4.9.6-1
- Update to NSPR_4_9_6_RTM

* Mon Feb 18 2013 Elio Maldonado <emaldona@redhat.com> - 4.9.5-2
- Resolves: rhbz#912483 - Add spec file support for AArch64

* Fri Feb 01 2013 Elio Maldonado <emaldona@redhat.com> - 4.9.5-1
- Update to NSPR_4_9_5_RTM

* Mon Dec 17 2012 Elio Maldonado <emaldona@redhat.com> - 4.9.4-1
- Update to NSPR_4_9_4_RTM

* Mon Oct 01 2012 Elio Maldonado <emaldona@redhat.com> - 4.9.3-0.1.beta1.1
- Update to NSPR_4_9_5_BETA1

* Sun Aug 26 2012 Elio Maldonado <emaldona@redhat.com> - 4.9.2-1
- Update to NSPR_4_9_2_RTM

* Fri Jul 20 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 4.9.1-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Wed Jul 11 2012 Elio Maldonado <emaldona@redhat.com> - 4.9.1-5
- Updated License: to MPLv2.0 per upstream

* Fri Jun 22 2012 Elio Maldonado <emaldona@redhat.com> - 4.9.1-4
- Update the nspr-config-pc.patch to prevent multilib regressions

* Thu Jun 21 2012 Elio Maldonado <emaldona@redhat.com> - 4.9.1-3
- Bump the release tag

* Thu Jun 21 2012 Elio Maldonado <emaldona@redhat.com> - 4.9.1-3
- Resolves: rhbz#833529 - restore the good changes to nspr.pc

* Thu Jun 21 2012 Elio Maldonado <emaldona@redhat.com> - 4.9.1-2
- Resolves: rhbz#833529 - revert unwanted change to nspr.pc
- Removed nspr-config.pc.in.patch

* Mon Jun 18 2012 Elio Maldonado <emaldona@redhat.com> - 4.9.1-1
- Update to NSPR_4_9_1_RTM

* Wed Mar 21 2012 Elio Maldonado <emaldona@redhat.com> - 4.9-2
- Resolves: Bug 805672 - Library needs partial RELRO support added

* Wed Feb 29 2012 Elio Maldonado <emaldona@redhat.com> - 4.9-1
- Update to NSPR_4_9_RTM

* Wed Jan 25 2012 Harald Hoyer <harald@redhat.com> 4.9-0.2.beta3.1
- install everything in /usr
  https://fedoraproject.org/wiki/Features/UsrMove

* Wed Jan 25 2012 Harald Hoyer <harald@redhat.com> 4.9-0.2.beta3.1
- 

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 4.9-0.2.beta3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Thu Oct 06 2011 Elio Maldonado <emaldona@redhat.com> - 4.9-0.1.beta3
- Update to NSPR_4_9_BETA3

* Thu Sep  8 2011 Ville Skyttä <ville.skytta@iki.fi> - 4.8.9-2
- Avoid %%post/un shell invocations and dependencies.

* Tue Aug 09 2011 Elio Maldonado <emaldona@redhat.com> - 4.8.9-1
- Update to NSPR_4_8_9_RTM

* Mon Jul 18 2011 Elio Maldonado <emaldona@redhat.com> - 4.8.8-4
- The tests must pass for the build to succeed

* Mon Jul 18 2011 Elio Maldonado <emaldona@redhat.com> - 4.8.8-3
- Run the nspr test suite in the %%check section

* Wed Jul 06 2011 Elio Maldonado <emaldona@redhat.com> - 4.8.8-2
- Conditionalize Thumb2 build support on right Arm arches

* Fri May 06 2011 Elio Maldonado <emaldona@redhat.com> - 4.8.8-1
- Update to NSPR_4_8_8_RTM

* Mon Apr 25 2011 Elio Maldonado Batiz <emaldona@redhat.com> - 4.8.8-0.1.beta3
- Update to NSPR_4_8_8_BETA3

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 4.8.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Wed Jan 12 2011 Elio Maldonado <emaldona@redhat.com> - 4.8.7-1
- Update to 4.8.7

* Mon Dec 27 2010 Elio Maldonado <emaldona@redhat.com> - 4.8.7-0.1beta2
- Rebuilt according to fedora pre-release naming guidelines

* Fri Dec 10 2010 Elio Maldonado <emaldona@redhat.com> - 4.8.6.99.2-1
- Update to NSPR_4_8_7_BETA2

* Tue Dec 07 2010 Elio Maldonado <emaldona@redhat.com> - 4.8.6.99.1-1
- Update to NSPR_4_8_7_BETA1

* Mon Aug 16 2010 Elio Maldonado <emaldona@redhat.com> - 4.8.6-1
- Update to 4.8.6

* Fri Mar 12 2010 Till Maas <opensource@till.name> - 4.8.4-2
- Fix release value

* Tue Feb 23 2010 Elio Maldonado <emaldona@redhat.com> - 4.8.4-1
- Update to 4.8.4

* Sat Nov 14 2009 Elio Maldonado<emaldona@redhat.com> - 4.8.2-3
- update to 4.8.2

* Sat Jul 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 4.8-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Tue Jun 30 2009 Christopher Aillon <caillon@redhat.com> 4.8-1
- update to 4.8

* Fri Jun 05 2009 Kai Engert <kaie@redhat.com> - 4.7.4-2
- update to 4.7.4

* Wed Mar 04 2009 Kai Engert <kaie@redhat.com> - 4.7.3-5
- add a workaround for bug 487844

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 4.7.3-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Wed Dec  3 2008 Ignacio Vazquez-Abrams <ivazqueznet+rpm@gmail.com> - 4.7.3-3
- Rebuild for pkgconfig

* Wed Nov 19 2008 Kai Engert <kaie@redhat.com> - 4.7.3-2
- update to 4.7.3
* Thu Oct 23 2008 Kai Engert <kaie@redhat.com> - 4.7.2-2
- update to 4.7.2

* Thu Oct  9 2008 Tom "spot" Callaway <tcallawa@redhat.com> - 4.7.1-5
- forgot to cvs add patch... whoops. :/

* Thu Oct  9 2008 Tom "spot" Callaway <tcallawa@redhat.com> - 4.7.1-4
- properly handle sparc64 in nspr code

* Tue Sep 30 2008 Dennis Gilmore <dennis@ausil.us> - 4.7.1-3
- add sparc64 to the list of 64 bit arches

* Mon Jun 02 2008 Kai Engert <kengert@redhat.com> - 4.7.1-2
- Update to 4.7.1

* Thu Mar 20 2008 Jesse Keating <jkeating@redhat.com> - 4.7.0.99.2-2
- Drop the old obsoletes/provides that aren't needed anymore.

* Mon Mar 17 2008 Kai Engert <kengert@redhat.com> - 4.7.0.99.2-1
- Update to NSPR_4_7_1_BETA2
* Tue Feb 26 2008 Kai Engert <kengert@redhat.com> - 4.7.0.99.1-2
- Addressed cosmetic review comments from bug 226202
* Fri Feb 22 2008 Kai Engert <kengert@redhat.com> - 4.7.0.99.1-1
- Update to NSPR 4.7.1 Beta 1
- Use /usr/lib{64} as devel libdir, create symbolic links.
* Sat Feb 09 2008 Kai Engert <kengert@redhat.com> - 4.7-1
- Update to NSPR 4.7

* Thu Jan 24 2008 Kai Engert <kengert@redhat.com> - 4.6.99.3-1
* NSPR 4.7 beta snapshot 20080120

* Mon Jan 07 2008 Kai Engert <kengert@redhat.com> - 4.6.99-2
- move .so files to /lib

* Wed Nov 07 2007 Kai Engert <kengert@redhat.com> - 4.6.99-1
- NSPR 4.7 alpha

* Tue Aug 28 2007 Kai Engert <kengert@redhat.com> - 4.6.7-3
- Updated license tag

* Fri Jul 06 2007 Kai Engert <kengert@redhat.com> - 4.6.7-2
- Update to 4.6.7

* Fri Jul 06 2007 Kai Engert <kengert@redhat.com> - 4.6.6-2
- Update thread-cleanup patch to latest upstream version
- Add upstream patch to support PR_STATIC_ASSERT

* Wed Mar 07 2007 Kai Engert <kengert@redhat.com> - 4.6.6-1
- Update to 4.6.6
- Adjust IPv6 patch to latest upstream version

* Sat Feb 24 2007 Kai Engert <kengert@redhat.com> - 4.6.5-2
- Update to latest ipv6 upstream patch
- Add upstream patch to fix a thread cleanup issue
- Now requires pkgconfig

* Mon Jan 22 2007 Wan-Teh Chang <wtchang@redhat.com> - 4.6.5-1
- Update to 4.6.5

* Tue Jan 16 2007 Kai Engert <kengert@redhat.com> - 4.6.4-2
- Include upstream patch to fix ipv6 support (rhbz 222554)

* Tue Nov 21 2006 Kai Engert <kengert@redhat.com> - 4.6.4-1
- Update to 4.6.4

* Thu Sep 14 2006 Kai Engert <kengert@redhat.com> - 4.6.3-1
- Update to 4.6.3

* Wed Jul 12 2006 Jesse Keating <jkeating@redhat.com> - 4.6.2-1.1
- rebuild

* Fri May 26 2006 Kai Engert <kengert@redhat.com> - 4.6.2-1
- Update to 4.6.2
- Tweak nspr-config to be identical on all platforms.

* Fri Feb 10 2006 Jesse Keating <jkeating@redhat.com> - 4.6.1-2.2
- bump again for double-long bug on ppc(64)

* Tue Feb 07 2006 Jesse Keating <jkeating@redhat.com> - 4.6.1-2.1
- rebuilt for new gcc4.1 snapshot and glibc changes

* Thu Jan  5 2006 Kai Engert <kengert@redhat.com> 4.6.1-2
- Do not use -ansi when compiling, because of a compilation
  problem with latest glibc and anonymous unions.
  See also bugzilla.mozilla.org # 322427.

* Wed Jan  4 2006 Kai Engert <kengert@redhat.com>
- Add an upstream patch to fix gcc visibility issues.

* Tue Jan  3 2006 Christopher Aillon <caillon@redhat.com>
- Stop shipping static libraries; NSS and dependencies no longer
  require static libraries to build.

* Thu Dec 15 2005 Christopher Aillon <caillon@redhat.com> 4.6.1-1
- Update to 4.6.1

* Fri Dec 09 2005 Jesse Keating <jkeating@redhat.com>
- rebuilt

* Fri Jul 15 2005 Christopher Aillon <caillon@redhat.com> 4.6-4
- Use the NSPR version numbering scheme reported by NSPR,
  which unfortunately is not exactly the same as the real
  version (4.6 != 4.6.0 according to RPM and pkgconfig).

* Fri Jul 15 2005 Christopher Aillon <caillon@redhat.com> 4.6-3
- Correct the CFLAGS reported by pkgconfig

* Tue Jul 12 2005 Christopher Aillon <caillon@redhat.com> 4.6-2
- Temporarily include the static libraries allowing nss and 
  its dependencies to build. 

* Tue Jul 12 2005 Christopher Aillon <caillon@redhat.com> 4.6-1
- Update to NSPR 4.6

* Wed Apr 20 2005 Christopher Aillon <caillon@redhat.com> 4.4.1-2
- NSPR doesn't have make install, but it has make real_install.  Use it.

* Thu Apr 14 2005 Christopher Aillon <caillon@redhat.com> 4.4.1-1
- Let's make an RPM.
