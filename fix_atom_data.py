import h5py
import numpy as np
import shutil
import os

def decode(v):
    if isinstance(v, (bytes, np.bytes_)):
        return v.decode('utf-8')
    elif isinstance(v, np.ndarray) and v.dtype.kind == 'S':
        return v.astype('U')
    return v

def fix_file(src, output_dir):
    filename = os.path.basename(src)
    dst = os.path.join(output_dir, filename)
    shutil.copy2(src, dst)
    try:
        with h5py.File(dst, 'r+') as f:
            for k, v in f.attrs.items():
                fixed = decode(v)
                if fixed is not v:
                    f.attrs[k] = fixed
            def fix_attrs(name, obj):
                for k, v in obj.attrs.items():
                    fixed = decode(v)
                    if fixed is not v:
                        obj.attrs[k] = fixed
            f.visititems(fix_attrs)

        with h5py.File(dst, 'r+') as f:
            if f.attrs.get('encoding', None) == 'N.':
                f.attrs['encoding'] = 'UTF-8'
            def fix_encoding(name, obj):
                if obj.attrs.get('encoding', None) == 'N.':
                    obj.attrs['encoding'] = 'UTF-8'
            f.visititems(fix_encoding)

        print(f"Fixed: {dst}")
        assert_string_attrs(dst)

    except AssertionError as e:
        print(f"ASSERTION FAILED: {dst} — {e}")
    except Exception as e:
        if os.path.exists(dst):
            os.remove(dst)
        print(f"FAILED: {src} — {e}")


def assert_string_attrs(path):
    failures = []

    def check_attrs(location_name, attrs):
        for k, v in attrs.items():
            if isinstance(v, (bytes, np.bytes_)):
                failures.append(f"  [{location_name}] attr '{k}' is still bytes: {v!r}")
            elif isinstance(v, np.ndarray) and v.dtype.kind == 'S':
                failures.append(f"  [{location_name}] attr '{k}' is still a byte-string array: dtype={v.dtype}")

    with h5py.File(path, 'r') as f:
        check_attrs("/ (root)", f.attrs)
        def visit_check(name, obj):
            check_attrs(name, obj.attrs)
        f.visititems(visit_check)

    if failures:
        raise AssertionError(
            f"Non-string attributes remain in {path}:\n" + "\n".join(failures)
        )
    else:
        print(f"  ✓ All attributes properly decoded in: {os.path.basename(path)}")


if __name__ == "__main__":
    src_dir = '/home/rishmitar/tardisDev/tardis-regression-data/atom_data'
    out_dir = '/home/rishmitar/tardisDev/tardis-regression-data/atom_data_fixed'

    os.makedirs(out_dir, exist_ok=True)

    h5_files = [
        os.path.join(src_dir, f)
        for f in os.listdir(src_dir)
        if f.endswith(".h5")
    ]

    if not h5_files:
        print("No .h5 files found.")
    else:
        for path in h5_files:
            fix_file(path, out_dir)