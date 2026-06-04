#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author: LAD021
Date: 2024/9/13
Description: <<<Enter your description here>>>.
"""
import fire


def run(
    path: str,
    output: str,
    verbose: bool = True,
    verbose_path: str = "verbose",
    ckt_type: str = "",
    validation: bool = True,
):
    from ci2n.app import main
    main(path, output, verbose, verbose_path, ckt_type, validation)


if __name__ == '__main__':
    fire.Fire(run)
