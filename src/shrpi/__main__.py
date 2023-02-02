import shrpi.cli
import shrpi.daemon


def daemon():
    shrpi.daemon.main()


def cli():
    shrpi.cli.main()


daemon()
