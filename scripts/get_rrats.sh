#!/bin/bash

PARENT_DIRECTORY="./known_rrats"

source ./logging.sh

########
# Download sources and place them in the correct directories
#
# Globals:
#   parsed_sources
#   obs_date
#
# Arguments:
#   None
#
# Outputs:
#   Download progress information
########
function download_sources() {

  for source in ${parsed_sources[@]}; do

    INFO "Downloading source ${source}..."

    while IFS= read -r source_line; do
      
      tpn_node=$( echo "${source_line}" | sed 's/^\(tpn-0-[0-9]\{1,2\}\).*/\1/')
      full_dir=$( echo "${source_line}" | sed 's/.*\(\/state.*\)\/allowed_known_sources.dat.*/\1/')
      time_dir=$( echo "${full_dir}" | sed 's/.*output\/\(.*\)\/beam.*/\1/' )
      beam_dir=$( echo ${source_line} | awk -F ' ' '{print $6$7}')
      filterbank=$( echo ${source_line} | awk -F ' ' '{print $10}')

      target_directory="${PARENT_DIRECTORY}/${source}/${time_dir}/${beam_dir}"

      INFO "Getting ${tpn_node}:${full_dir}/${filterbank} into ${target_directory}"

      mkdir -p "${target_directory}"
      chmod 777 -R "${target_directory}"

      rsync --progress -e "ssh tuse ssh" ${tpn_node}:${full_dir}/${filterbank} ${target_directory}
      rsync --progress -e "ssh tuse ssh" ${tpn_node}:${full_dir}/Plots/used_candidates.spccl.extra ${target_directory}
      rsync --progress -e "ssh tuse ssh" ${tpn_node}:${full_dir}/../run_summary.json ${target_directory}
    
    done < <( ssh tuse /bin/bash -s << EOF
    rocks run host "grep -H ${source} /state/partition1/node_controller/output/${obs_date}*/beam*/allowed_known_sources.dat 2> /dev/null" collate=true \
      | grep -v ": command" \
      | grep -v "down" \
      | sort \
      | uniq
EOF
)

  done

}

########
# List sources for a given day.
#
# Globals:
#   obs_date
#
# Arguments:
#   None
#
# Outputs:
#   List of RRATs detected in a given day.
########
function list_sources() {

  available_sources=$( ssh tuse /bin/bash -s << EOF
    rocks run host "cat /state/partition1/node_controller/output/${obs_date}*/beam*/allowed_known_sources.dat 2> /dev/null" \
      | grep -v ": command" \
      | grep -v "down" \
      | awk -F ' ' '{print \$NF}' \
      | sort \
      | uniq
EOF
)

  if [[ -n "${available_sources}" ]]; then

    INFO "The following sources were found:"
    for source in ${available_sources}; do
      echo "${source}"
    done

  else

    WARNING "No sources were found"

  fi

}

########
# Parse comma-separated source and put them in an array.
#
# Globals:
#   parsed_sources
#
# Arguments:
#   None
# 
# Outputs:
#   List of parsed sources.
########
function parse_sources() {

  OLDIFS="${IFS}"
  IFS=","
  for source in ${source_list}; do
    parsed_sources[${#parsed_sources[@]}]="${source}"
  done

  INFO "Sources that will be downloaded:"
  for source in ${parsed_sources[@]}; do
    echo "  ${source}"
  done
  IFS="${OLDIFS}"

}

########
# Print out the help message, describing all of the command line
# options.
#
# Arguments:
#   None
#
# Outputs:
#   Help information.
########
function help() {

  echo "Get known rrats"
  echo
  echo "Usage ./get_rrats.sh -d <date> [OPTIONS]"
  echo
  INFO "Available options:"
  echo "-h print this message"
  echo "-d date to process in the format yyyy-mm-dd - REQUIRED"
  echo "-l list available known RRAT detections"
  echo "-s comma-separated list of sources to download"
  echo
  exit 0
}

function main() {

  local optstring=":hld:s:"
  list_only=false

  while getopts "${optstring}" arg; do

    case "${arg}" in
      h) help ;;
      d) obs_date="${OPTARG}" ;;
      l) list_only=true ;;
      s) source_list="${OPTARG}" ;;
      ?) 
        ERROR "Invalid option ${OPTARG}"
        help
        exit 1
        ;;
    
    esac

  done 

  if [[ -z "${obs_date}" ]]; then
    ERROR "Observation data not specified!"
    exit 1
  fi

  if [[ "${list_only}" == true ]]; then
    INFO "Will list the sources"

    list_sources

    exit 0
  else 

    if [[ -z "${source_list}" ]]; then
      ERROR "Source list not specified!"
      exit 1
    
    else
      declare -a parsed_sources

      parse_sources
      download_sources

    fi

  fi



}

main "$@"