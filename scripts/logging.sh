#!/bin/bash

INF="\033[1m"
WRN="\033[1;33m"
ERR="\033[1;31m"
RST="\033[0m"

function WARNING()
{
  local message=$1
  echo -e "${WRN}$(date): ${message}${RST}"
}

function ERROR()
{
  local message=$1
  echo -e "${ERR}$(date): ${message}${RST}" 1>&2
}

function INFO()
{
  local message=$1
  echo -e "${INF}$(date): ${message}${RST}"
}