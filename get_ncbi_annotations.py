import ftplib
import re
import sys

FTP_URL = "ftp.ncbi.nlm.nih.gov"
DIR = "/genomes/all"


def read_accessions(filepath):
    with open(filepath, 'r') as f:
        return [line.strip() for line in f if line.strip()]


def ftp_connect():
    ftp = ftplib.FTP(FTP_URL, timeout=10)
    ftp.login()
    return ftp


def list_directories(ftp, path, pattern):
    try:
        ftp.cwd(path)
        files = ftp.nlst()
        matched = [f for f in files if re.match(pattern, f)]
        return matched[0].rstrip('@') if matched else None
    except Exception:
        return None


def list_gff_files(ftp, path, accession):
    try:
        ftp.cwd(path)
        files = ftp.nlst()
        return [f for f in files if f.endswith('.gff.gz') and f.startswith(accession)]
    except Exception:
        return []


def main(accession_file, output_file):
    accessions = read_accessions(accession_file)

    with open(output_file, 'w') as out:
        ftp = ftp_connect()

        try:
            for accession in accessions:
                base_path = f"{DIR}/{accession[:3]}/{accession[4:7]}/{accession[7:10]}/{accession[10:13]}"

                dir_to_cd = list_directories(ftp, base_path, rf'^{accession}')

                if not dir_to_cd:
                    continue

                full_path = f"{base_path}/{dir_to_cd}"

                gff_files = list_gff_files(ftp, full_path, accession)

                if not gff_files:
                    continue

                https_base = f"https://{FTP_URL}{full_path}"
                for gff_file in gff_files:
                    gff_url = f"{https_base}/{gff_file}"
                    out.write(f"{accession}\t{gff_url}\n")

        finally:
            try:
                ftp.quit()
            except (EOFError, ftplib.error_proto):
                print("FTP connection already closed.")

# Example usage
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <accession_file> <output_file>")
        sys.exit(1)

    accession_file = sys.argv[1]
    output_file = sys.argv[2]

    main(accession_file, output_file)
