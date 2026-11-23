%global debug_package %{nil}
%global _find_debuginfo_opts --no-ar-files
Summary:	Glasgow Haskell Compiler 9.12.4 (bootstrapped with in-chain GHC 9.8.4)
Name:		ghc912
Version:	9.12.4
Release:	1
License:	BSD
Group:		Development/Other
Url:		https://www.haskell.org/ghc/
# Complement package. Does not replace distro ghc, so no Epoch.
# The host is packaged ghc98 (GHC 9.8.4). Hadrian dependencies,
# happy, and alex are in the bootstrap kit. This spec compiles the
# 9.12.4 sources; it does not copy a prebuilt prefix.
ExclusiveArch:	x86_64 znver1
Source0:	ghc-9.12.4-src.tar.xz
Source1:	ghc912-bootstrap-kit.tar.gz
Source2:	ghc912-build.sh
Source3:	%{name}.rpmlintrc

BuildRequires:	ghc98
BuildRequires:	make
BuildRequires:	python
BuildRequires:	perl
BuildRequires:	autoconf
BuildRequires:	patch
BuildRequires:	gcc
BuildRequires:	lld
BuildRequires:	diffutils
BuildRequires:	binutils
BuildRequires:	pkgconfig(gmp)
BuildRequires:	pkgconfig(ncurses)
BuildRequires:	pkgconfig(libffi)
BuildRequires:	pkgconfig(numa)
BuildRequires:	file
BuildRequires:	tar
BuildRequires:	xz
BuildRequires:	gzip

%description
GHC 9.12.4 compiled from its Haskell sources by packaged GHC 9.8.4
(Hadrian, static libraries, host GMP). No upstream bindist and no
GHCup compiler.

Installed as ghc912 / ghc-9.12.4 so it can coexist with ghc98 and a
distro GHC.

%prep
set -eu
cd %{_builddir}
rm -rf ghc912-root
mkdir -p ghc912-root
tar -xJf %{SOURCE0} -C ghc912-root
tar -xzf %{SOURCE1} -C ghc912-root
test -d ghc912-root/ghc-9.12.4/hadrian/bootstrap
test "$(tr -d '[:space:]' < ghc912-root/ghc-9.12.4/VERSION)" = "9.12.4"
test -f ghc912-root/bootstrap/plan-bootstrap-9_8_4.json
test -f ghc912-root/bootstrap/regen-parsers.sh
test -f ghc912-root/bootstrap/cmp-regenerated.sh
test -d ghc912-root/bootstrap/hadrian
test -f ghc912-root/bootstrap/happy-1.20.1.1.tar.gz
test -f ghc912-root/bootstrap/alex-3.2.7.4.tar.gz
test -f %{SOURCE2}
set +u

%build
set -eu
bash %{SOURCE2} "%{_builddir}/ghc912-root"
set +u

%install
set -eu
dest=%{_builddir}/ghc912-root/dest
if [ -d "$dest/lib/ghc-9.12.4" ]; then
	src=$dest/lib/ghc-9.12.4
elif [ -d "$dest/lib64/ghc-9.12.4" ]; then
	src=$dest/lib64/ghc-9.12.4
else
	echo "ghc912: install tree has no lib/ghc-9.12.4" >&2
	exit 1
fi
mkdir -p %{buildroot}%{_libdir} %{buildroot}%{_bindir}
cp -a "$src" %{buildroot}%{_libdir}/ghc-9.12.4
test -x %{buildroot}%{_libdir}/ghc-9.12.4/bin/ghc-9.12.4
file %{buildroot}%{_libdir}/ghc-9.12.4/bin/ghc-9.12.4 | grep -q ELF
test -f %{buildroot}%{_libdir}/ghc-9.12.4/lib/settings
test -x %{buildroot}%{_libdir}/ghc-9.12.4/bin/host-gcc
libname=$(basename %{_libdir})
cat > %{buildroot}%{_bindir}/ghc912 << EOF
#!/bin/sh
if [ -x "\$0" ] && [ "\$0" != "\${0#*/}" ]; then
	arg0=\$0
else
	arg0=\$(command -v "\$0") || exit 1
fi
here=\$(CDPATH= cd -- "\$(dirname "\$arg0")" && pwd)
root=\$(dirname "\$here")
exec "\$root/$libname/ghc-9.12.4/bin/ghc-9.12.4" -B"\$root/$libname/ghc-9.12.4/lib" "\$@"
EOF
cat > %{buildroot}%{_bindir}/ghc-pkg912 << EOF
#!/bin/sh
if [ -x "\$0" ] && [ "\$0" != "\${0#*/}" ]; then
	arg0=\$0
else
	arg0=\$(command -v "\$0") || exit 1
fi
here=\$(CDPATH= cd -- "\$(dirname "\$arg0")" && pwd)
root=\$(dirname "\$here")
top="\$root/$libname/ghc-9.12.4"
exec "\$top/bin/ghc-pkg-9.12.4" --global-package-db "\$top/lib/package.conf.d" "\$@"
EOF
chmod 755 %{buildroot}%{_bindir}/ghc912 %{buildroot}%{_bindir}/ghc-pkg912
ln -sfn ghc912 %{buildroot}%{_bindir}/ghc-9.12.4
ln -sfn ghc-pkg912 %{buildroot}%{_bindir}/ghc-pkg-9.12.4
set +u

%files
%{_bindir}/ghc912
%{_bindir}/ghc-pkg912
%{_bindir}/ghc-9.12.4
%{_bindir}/ghc-pkg-9.12.4
%{_libdir}/ghc-9.12.4/

%check
set -eu
cd %{_builddir}
export PATH=%{buildroot}%{_bindir}:$PATH
hash -r
command -v ghc912 | grep -q '%{buildroot}'
b=$(command -v ghc912)
g=%{buildroot}%{_libdir}/ghc-9.12.4
test -x "$g/bin/ghc-9.12.4"
file "$g/bin/ghc-9.12.4" | grep -q ELF
test -f "$g/lib/settings"
test -x "$g/bin/host-gcc"
"$b" --numeric-version | tee numeric.out
test "$(cat numeric.out)" = "9.12.4"
"$b" --numeric-version | tee numeric2.out
test "$(cat numeric2.out)" = "9.12.4"
cat > Helper.hs << 'EOF'
module Helper (sumList) where

sumList :: [Int] -> Int
sumList [] = 0
sumList (x:xs) = x + sumList xs
EOF
cat > Main.hs << 'EOF'
module Main where

import Helper

main :: IO ()
main = do
	let xs = [1, 2, 3, 4]
	putStrLn (show (sumList xs))
EOF
rm -rf sum-a sum-b
mkdir sum-a sum-b
cp Helper.hs Main.hs sum-a/
cp Helper.hs Main.hs sum-b/
( cd sum-a && "$b" -v0 --make Main.hs -o sum10 && ./sum10 ) > sum-a.out
test "$(cat sum-a.out)" = "10"
( cd sum-b && "$b" -v0 --make Main.hs -o sum10 && ./sum10 ) > sum-b.out
test "$(cat sum-b.out)" = "10"
set +u
