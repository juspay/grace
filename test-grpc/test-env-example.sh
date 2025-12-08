#!/usr/bin/env bash

# Example: How to set environment variables correctly

# Set credentials (note: KEY1 not KEY_1)
export BAMBORA_AUTH_TYPE="body-key"
export BAMBORA_API_KEY="18Fb10c3ad614D2694BC88bC74C43FFD"
export BAMBORA_KEY1="300213193"
export BAMBORA_MERCHANT_ID="test_merchant_bambora"

# Run the test
cd /Users/yashasvi.kapil/grace-main/grace/test-grpc
./test-connector.sh bambora --set 1
