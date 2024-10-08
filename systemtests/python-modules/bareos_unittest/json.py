#!/usr/bin/env python
#
#   BAREOS - Backup Archiving REcovery Open Sourced
#
#   Copyright (C) 2019-2024 Bareos GmbH & Co. KG
#
#   This program is Free Software; you can redistribute it and/or
#   modify it under the terms of version three of the GNU Affero General Public
#   License as published by the Free Software Foundation and included
#   in the file LICENSE.
#
#   This program is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#   Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
#   02110-1301, USA.

# -*- coding: utf-8 -*-

import json
import logging
import os
import re
import subprocess
from time import sleep
import unittest
import warnings

import bareos.bsock
from bareos.bsock.constants import Constants
from bareos.bsock.protocolmessages import ProtocolMessages
from bareos.bsock.protocolversions import ProtocolVersions
from bareos.bsock.lowlevel import LowLevel
import bareos.exceptions

from bareos_unittest.base import Base as PythonBareosBase


class Json(PythonBareosBase):

    #
    # Util
    #

    @staticmethod
    def check_resource(director, resourcesname, name):
        logger = logging.getLogger()
        rc = False
        try:
            # .<resourcesname> only returns one result key,
            # but that can differ slightly from the called command,
            # e.g. ".console" returns
            # "result": { "consoles": [ ... ] }
            # Therefore we check "all" keys of result
            # and do a substring match.
            result = director.call(".{}".format(resourcesname))
            for resourcetype in result.keys():
                if resourcetype.startswith(resourcesname):
                    for i in result[resourcetype]:
                        if i["name"] == name:
                            rc = True
        except Exception as e:
            logger.warning(str(e))
        return rc

    @staticmethod
    def check_console(director, name):
        return PythonBareosJsonBase.check_resource(director, "consoles", name)

    @staticmethod
    def check_jobname(director, name):
        return PythonBareosJsonBase.check_resource(director, "jobs", name)

    def configure_add(self, director, resourcesname, resourcename, cmd):
        if not self.check_resource(director, resourcesname, resourcename):
            result = director.call("configure add {}".format(cmd))
            self.assertEqual(result["configure"]["add"]["name"], resourcename)
            self.assertTrue(
                self.check_resource(director, resourcesname, resourcename),
                "Failed to find resource {} in {}.".format(resourcename, resourcesname),
            )

    def wait_job(self, director, jobId, expected_status="OK"):
        result = director.call("wait jobid={}".format(jobId))
        # "result": {
        #    "job": {
        #    "jobid": 1,
        #    "jobstatuslong": "OK",
        #    "jobstatus": "T",
        #    "exitstatus": 0
        #    }
        # }
        self.assertEqual(result["job"]["jobstatuslong"], expected_status)

    def run_job(
        self, director, jobname, level=None, fileset=None, extra=None, wait=False
    ):
        logger = logging.getLogger()
        run_parameter = [f"job={jobname}"]
        if level:
            run_parameter.append(f"level={level}")
        if fileset:
            run_parameter.append(f"fileset={fileset}")
        if extra:
            run_parameter.append("{}".format(extra))
        run_parameter.append("yes")
        run_cmd = "run {}".format(" ".join(run_parameter))
        result = director.call(run_cmd)
        jobId = result["run"]["jobid"]
        if wait:
            self.wait_job(director, jobId)
        return jobId

    def run_restore(
        self,
        director,
        client,
        jobname=None,
        jobid=None,
        fileset=None,
        extra=None,
        wait=False,
    ):
        logger = logging.getLogger()
        use_select = True
        run_parameter = ["client={}".format(client)]
        if jobname:
            run_parameter.append("restorejob={}".format(jobname))
        if jobid:
            run_parameter.append("jobid={}".format(jobid))
            use_select = False
        if fileset:
            run_parameter.append("fileset={}".format(fileset))
        if extra:
            run_parameter.append("{}".format(extra))
        if use_select:
            run_parameter.append("select")
        run_parameter += ["all", "done", "yes"]
        restore_cmd = "restore {}".format(" ".join(run_parameter))
        result = director.call(restore_cmd)
        jobId = result["run"]["jobid"]
        if wait:
            self.wait_job(director, jobId)
        return jobId

    def get_backup_jobid(self, director, jobname, level=None, fileset=None, extra=None):
        """
        Get a valid backup job jobid.
        If no such job exists,
        run such a job.
        """
        list_level_parameter = ""
        if level:
            list_level_parameter = f"level={level}"
        result = director.call(
            f"list jobs job={jobname} {list_level_parameter} jobstatus=T last"
        )
        if len(result["jobs"]) >= 1:
            job = result["jobs"][0]
            # TODO: it would be more efficient, if the list command could filter by fileset.
            if (fileset is None) or (job["fileset"] == fileset):
                return job["jobid"]
        # there is no valid backup for these parameters.
        # run a backup job.
        return self.run_job(director, jobname, level, fileset, extra, wait=True)

    def _test_job_result(self, jobs, jobid):
        logger = logging.getLogger()
        for job in jobs:
            if job["jobid"] == jobid:
                files = int(job["jobfiles"])
                logger.debug("Job {} contains {} files.".format(jobid, files))
                self.assertTrue(files >= 1, "Job {} contains no files.".format(jobid))
                return True
        self.fail("Failed to find job {}".format(jobid))
        # add return to prevent pylint warning
        return False

    def _test_no_volume_in_pool(self, console, password, pool):
        logger = logging.getLogger()
        bareos_password = bareos.bsock.Password(password)
        console_poolbotfull = bareos.bsock.DirectorConsoleJson(
            address=self.director_address,
            port=self.director_port,
            name=console,
            password=bareos_password,
            **self.director_extra_options,
        )

        result = console_poolbotfull.call("llist media all")
        logger.debug(str(result))

        self.assertGreaterEqual(len(result["volumes"]), 1)

        for volume in result["volumes"]:
            self.assertNotEqual(volume["pool"], pool)

        return True

    def _test_list_with_valid_jobid(self, director, jobid):
        for cmd in ["list", "llist"]:
            result = director.call("{} jobs".format(cmd))
            self._test_job_result(result["jobs"], jobid)

            listcmd = "{} jobid={}".format(cmd, jobid)
            result = director.call(listcmd)
            self._test_job_result(result["jobs"], jobid)

    def _test_list_with_invalid_jobid(self, director, jobid):
        for cmd in ["list", "llist"]:
            result = director.call("{} jobs".format(cmd))
            with self.assertRaises(AssertionError):
                self._test_job_result(result["jobs"], jobid)

            listcmd = "{} jobid={}".format(cmd, jobid)
            result = director.call(listcmd)
            self.assertEqual(
                len(result["jobs"]),
                0,
                "Command {} should not return results. Current result: {} visible".format(
                    listcmd, str(result)
                ),
            )

    def search_joblog(self, director, jobId, patterns):

        if isinstance(patterns, list):
            pattern_dict = {i: False for i in patterns}
        else:
            pattern_dict = {patterns: False}

        result = director.call("list joblog jobid={}".format(jobId))
        joblog_list = result["joblog"]

        found = False
        for pattern in pattern_dict:
            for logentry in joblog_list:
                if re.search(pattern, logentry["logtext"]):
                    pattern_dict[pattern] = True
            self.assertTrue(
                pattern_dict[pattern],
                'Failed to find pattern "{}" in Job Log of Job {}.'.format(
                    pattern, jobId
                ),
            )

    def run_job_and_search_joblog(self, director, jobname, level, patterns):

        jobId = self.run_job(director, jobname, level, wait=True)
        self.search_joblog(director, jobId, patterns)
        return jobId

    def list_jobid(self, director, jobid):
        result = director.call("llist jobid={}".format(jobid))
        try:
            return result["jobs"][0]
        except KeyError:
            raise ValueError("jobid {} does not exist".format(jobid))
