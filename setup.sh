#!/usr/bin/env bash

if which pip >/dev/null; then
    echo "Found pip"
else
    echo "Installing pip"
    curl https://bootstrap.pypa.io/ez_setup.py -o - | sudo python
    easy_install pip
fi

echo "Upgrading pip"
pip install --upgrade pip

echo "============================================================="
echo ""
echo ""
echo "Installing dependencies"
pip install requests
pip install jmespath

echo "============================================================="
echo ""
echo ""
echo "Installing AWS cli"
if which aws >/dev/null; then
    echo "AWS cli already installed"
else
    pip install awscli
fi

echo "Upgrading AWS cli"
pip install --upgrade awscli

echo "============================================================="
echo ""
echo ""
echo "Setup is complete."
echo "============================================================="
echo ""
echo ""
echo "Run following to configure Production access to AWS:"
echo ""
echo "aws configure --profile prod"
echo ""
echo ""