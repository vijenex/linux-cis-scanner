Name:           vijenex-cis-scanner
Version:        1.0.0
Release:        1%{?dist}
Summary:        Enterprise Linux Security Compliance Scanner

License:        MIT
URL:            https://github.com/vijenex/linux-cis-scanner
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
Requires:       python3 >= 3.6

%description
Vijenex CIS Scanner is an enterprise-grade security compliance auditing tool
for Linux systems based on CIS (Center for Internet Security) benchmarks.
Similar to OpenSCAP, it provides automated security compliance scanning.

%prep
%setup -q

%build
# No build required for Python scripts

%install
rm -rf %{buildroot}

# Create directories
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/vijenex-cis
mkdir -p %{buildroot}%{_sysconfdir}/vijenex-cis
mkdir -p %{buildroot}%{_localstatedir}/log/vijenex-cis
mkdir -p %{buildroot}%{_mandir}/man1

# Install scanner components for all supported distributions
for distro_dir in rhel-8 rhel-9 centos-7; do
    if [ -d "$distro_dir" ]; then
        cp -r "$distro_dir" %{buildroot}%{_datadir}/vijenex-cis/
    fi
done

# Install wrapper script
install -m 0755 packaging/rpm/vijenex-cis-wrapper.sh %{buildroot}%{_bindir}/vijenex-cis

# Install documentation
cp LICENSE %{buildroot}%{_datadir}/vijenex-cis/
cp README.md %{buildroot}%{_datadir}/vijenex-cis/

# Install man page
install -m 0644 packaging/vijenex-cis.1 %{buildroot}%{_mandir}/man1/vijenex-cis.1

%files
%license LICENSE
%doc README.md
%{_bindir}/vijenex-cis
%{_datadir}/vijenex-cis/
%dir %{_sysconfdir}/vijenex-cis
%dir %{_localstatedir}/log/vijenex-cis
%{_mandir}/man1/vijenex-cis.1*

%post
# Update man database
if command -v mandb >/dev/null 2>&1; then
    mandb -q 2>/dev/null || true
fi

echo "=========================================================="
echo "  Vijenex CIS Scanner installed successfully!"
echo "=========================================================="
echo "Usage:"
echo "  sudo vijenex-cis                    # Complete scan"
echo "  sudo vijenex-cis --profile Level2   # Level 2 scan"
echo "  man vijenex-cis                     # Manual page"
echo "=========================================================="

%changelog
* Mon Dec 16 2024 Vijenex Team <support@vijenex.com> - 1.0.0-1
- Initial RPM release
- Support for RHEL 8, RHEL 9, CentOS 7
- CIS Benchmark compliance scanning
- HTML and CSV report generation
