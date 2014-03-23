#!/usr/bin/env python

import sys
import toutvcli.app


if __name__ == '__main__':
    args = sys.argv[1:]
    sys.exit(toutvcli.app.run(args))
