from nf.nf_service import NFService
from dotenv import load_dotenv

load_dotenv()

# from smp.smp_service import process_sequence_smp


def main():

    # NF
    # Start NF Service
    nf = NFService()
    nf.run_sequence()


if __name__ == "__main__":
    main()
