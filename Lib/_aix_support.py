"""Shared AIX support functions."""

import sys
import sysconfig

try:
    import subprocess
except ImportError:  # pragma: no cover
    # _aix_support is used in distutils by setup.py to build C extensions,
    # before subprocess dependencies like _posixsubprocess are available.
    import _bootsubprocess as subprocess


def _aix_tag(vrtl, bd):
    # type: (List[int], int) -> str
    # Infer the ABI bitwidth from maxsize (assuming 64 bit as the default)
    _sz = 32 if sys.maxsize == (2**31-1) else 64
    # vrtl[version, release, technology_level]
    return "aix-{:1x}{:1d}{:02d}-{:04d}-{}".format(vrtl[0], vrtl[1], vrtl[2], bd, _sz)


# extract version, release and technology level from a VRMF string
def _aix_vrtl(vrmf):
    # type: (str) -> List[int]
    v, r, tl = vrmf.split(".")[:3]
    return [int(v[-1]), int(r), int(tl)]


def _aix_bosmp64():
    # type: () -> Tuple[str, int]
    """
    Return a Tuple[str, int] e.g., ['7.1.4.34', 1806]
    The fileset bos.mp64 is the AIX kernel. It's VRMF and builddate
    reflect the current ABI levels of the runtime environment.
    """
    # We expect all AIX systems to have lslpp installed in this location
    out = subprocess.check_output(["/usr/bin/lslpp", "-Lqc", "bos.mp64"])
    out = out.decode("utf-8")
    out = out.strip().split(":")  # type: ignore
    # Use str() and int() to help mypy see types
    return (str(out[2]), int(out[-1]))


def aix_platform():
    # type: () -> str
    """
    AIX filesets are identified by four decimal values: V.R.M.F.
    V (version) and R (release) can be retreived using ``uname``
    Since 2007, starting with AIX 5.3 TL7, the M value has been
    included with the fileset bos.mp64 and represents the Technology
    Level (TL) of AIX. The F (Fix) value also increases, but is not
    relevant for comparing releases and binary compatibility.
    For binary compatibility the so-called builddate is needed.
    Again, the builddate of an AIX release is associated with bos.mp64.
    AIX ABI compatibility is described  as guaranteed at: https://www.ibm.com/\
    support/knowledgecenter/en/ssw_aix_72/install/binary_compatability.html

    For pep425 purposes the AIX platform tag becomes:
    "aix-{:1x}{:1d}{:02d}-{:04d}-{}".format(v, r, tl, builddate, bitsize)
    e.g., "aix-6107-1415-32" for AIX 6.1 TL7 bd 1415, 32-bit
    and, "aix-6107-1415-64" for AIX 6.1 TL7 bd 1415, 64-bit
    """
    vrmf, bd = _aix_bosmp64()
    return _aix_tag(_aix_vrtl(vrmf), bd)


# extract vrtl from the BUILD_GNU_TYPE as an int
def _aix_bgt():
    if gnu_type := sysconfig.get_config_var("BUILD_GNU_TYPE"):
        return _aix_vrtl(vrmf=gnu_type)
    else:
        raise ValueError("BUILD_GNU_TYPE is not defined")


def aix_buildtag():
    # type: () -> str
    """
    Return the platform_tag of the system Python was built on.
    """
    # AIX_BUILDDATE is defined by configure with:
    # lslpp -Lcq bos.mp64 | awk -F:  '{ print $NF }'
    build_date = sysconfig.get_config_var("AIX_BUILDDATE")
    try:
        build_date = int(build_date)
    except (ValueError, TypeError):
        raise ValueError(f"AIX_BUILDDATE is not defined or invalid: "
                         f"{build_date!r}")
    return _aix_tag(_aix_bgt(), build_date)
