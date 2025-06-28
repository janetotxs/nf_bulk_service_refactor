from nf.nf_service import NFService

# from smp.smp_service import process_sequence_smp


def main():

    # NF
    # Start NF Service
    nf = NFService()
    nf.run_sequence(fail_check=True)


if __name__ == "__main__":
    main()
