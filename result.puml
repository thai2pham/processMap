
@startuml total.png
left to right direction

skinparam usecase {
    BackgroundColor<< Execution >> YellowGreen
    BorderColor<< Execution >> YellowGreen

    BackgroundColor<< Email >> LightSeaGreen
    BorderColor<< Email >> LightSeaGreen

    ArrowColor Olive
}
        package source{
    usecase (service-manager) as (service-manager)
}
package python-data{
    usecase (info-doxygen-data.py) as (info-doxygen-data.py)
}
package perl-data{
    usecase (info-doxygen.gv) as (info-doxygen.gv)
}
package log{
    usecase (service-[name].log) as (service-[name].log)
    usecase (__result.txt) as (__result.txt)
}
package email{
    usecase ([$PROJECT_NAME] DailyTest report ${DATE_STR}) as ([$PROJECT_NAME] DailyTest report ${DATE_STR}) << Email >>
    usecase ([TIGER-INFRA TAF SLDD STATISTICS] sldd status for each model) as ([TIGER-INFRA TAF SLDD STATISTICS] sldd status for each model) << Email >>
    usecase (TAF SLDD result) as (TAF SLDD result) << Email >>
    usecase ([Weekly Report] your 7 days weekly report for your assigned) as ([Weekly Report] your 7 days weekly report for your assigned) << Email >>
}
package data{
    usecase (Alltestcase.txt) as (Alltestcase.txt)
    usecase (test_coverage_*.csv) as (test_coverage_*.csv)
    usecase (TestResultFile.txt) as (TestResultFile.txt)
}
  rectangle Fish{
  }
  rectangle info-doxygen{
    usecase (doxygen) as (doxygen) << Execution >>
    (service-manager) --> (doxygen) : get doxygen output from service manager souce code
    (doxygen) --> (info-doxygen-data.py) : get doxygen output from service manager souce code
    (doxygen) --> (info-doxygen.gv) : get doxygen output from service manager souce code
  }
  rectangle info-doxygen{
    usecase (info_doxygen.pl) as (info_doxygen.pl) << Execution >>
    (info-doxygen.gv) --> (info_doxygen.pl) : check whether it is the right doxygen comments
    (info_doxygen.pl) --> (service-[name].log) : check whether it is the right doxygen comments
  }
  rectangle AutoTest_Cmd{
    usecase (project:info-doxygen) as (project:info-doxygen) << Execution >>
    (common_job_for_upload.sh) --> (project:info-doxygen) : check whether it is the right doxygen comments
    (project:info-doxygen) --> (__result.txt) : check whether it is the right doxygen comments
  }
  rectangle AutoTest_Cmd{
    usecase (project:intuitiveui) as (project:intuitiveui) << Execution >>
    (job_for_email_report.sh) --> (project:intuitiveui) : result to html table
    (project:intuitiveui) --> ([$PROJECT_NAME] DailyTest report ${DATE_STR}) : result to html table
  }
  rectangle intuitiveui{
    usecase (intuitiveui.py) as (intuitiveui.py) << Execution >>
    (TestResultFile.txt) --> (intuitiveui.py) : result to html table
    (intuitiveui.py) --> ([$PROJECT_NAME] DailyTest report ${DATE_STR}) : result to html table
  }
  rectangle taf_sldd_statistics{
    usecase (get_sldd.py) as (get_sldd.py) << Execution >>
    (/var/www/html/DailyTest) --> (get_sldd.py) : TAF SLDD test report
    (Alltestcase.txt) --> (get_sldd.py) : TAF SLDD test report
    (test_coverage_*.csv) --> (get_sldd.py) : TAF SLDD test report
    (TestResultFile.txt) --> (get_sldd.py) : TAF SLDD test report
    (sldd_history.csv) --> (get_sldd.py) : TAF SLDD test report
    (get_sldd.py) --> (sldd_history.csv) : TAF SLDD test report
    (get_sldd.py) --> ([TIGER-INFRA TAF SLDD STATISTICS] sldd status for each model) : TAF SLDD test report
  }
  rectangle swit{
    usecase (swit.py) as (swit.py) << Execution >>
    (TestResult_SWIT.txt) --> (swit.py) : TestResult_SWIT.txt
    (swit.py) --> (TAF SLDD result) : TestResult_SWIT.txt
    (swit.py) --> (TestResult_SWIT.html) : TestResult_SWIT.txt
  }
  rectangle weekly_work_report_from_jira{
    usecase (get_work.py) as (get_work.py) << Execution >>
    (VLM) --> (get_work.py) : weekly report for developers from VLM and CodeBeamer
    (CodeBeamber) --> (get_work.py) : weekly report for developers from VLM and CodeBeamer
    (get_work.py) --> ([Weekly Report] your 7 days weekly report for your assigned) : weekly report for developers from VLM and CodeBeamer
  }
@enduml
