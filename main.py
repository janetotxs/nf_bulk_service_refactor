from nf.nf_service import NFService

# from smp.smp_service import process_sequence_smp


def main():

    nf = NFService()
    # NF
    # Start NF Service
    nf.run_sequence()

    # SMP
    # process_sequence_smp()


if __name__ == "__main__":
    main()
