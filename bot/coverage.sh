#!/bin/bash
set -e

coverage run -m pytest
coverage $1