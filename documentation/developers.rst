.. raw:: latex

    \clearpage
	
.. _developers:

Software quality assurance
=======================================

The following section includes information about 
the WNTR software repository, 
software tests,
documentation, 
examples, 
bug reports,
feature requests, and
ways to contribute.
Developers should follow the :ref:`developer_instructions` to 
clone and setup WNTR.

GitHub repository
---------------------
WNTR is maintained in a version controlled repository.  
WNTR is hosted on US EPA GitHub organization at https://github.com/USEPA/WNTR.

.. _software_tests:

Software tests
--------------------
WNTR includes continuous integration software tests that are run using GitHub Actions.
Travis CI and AppVeyor are used by the core development team as secondary testing services.
The tests are run each time changes are made to the repository.  
The tests cover a wide range of unit and 
integration tests designed to ensure that the code is performing as expected.  
New tests are developed each time new functionality is added to the code.   
Testing status (passed/failed) and code coverage statistics are posted on 
the README section at https://github.com/USEPA/WNTR.
	
Tests can also be run locally using the Python package pytest.  
For more information on pytest, see  https://docs.pytest.org/.
The pytest package comes with a command line software tool.
Tests can be run in the WNTR directory using the following command in a command line/PowerShell prompt::

	pytest wntr

In addition to the publicly available software tests run using GitHub Actions,
WNTR is also tested on private servers using several large water utility network models.
	
Documentation
---------------------
WNTR includes a user manual that is built using the Read the Docs service.
The user manual is automatically rebuilt each time changes are made to the code.
The documentation is publicly available at https://usepa.github.io/WNTR/.
The user manual includes an overview, installation instructions, simple examples, 
and information on the code structure and functions.  
WNTR includes documentation on the API for all 
public functions, methods, and classes.
New content is marked `Draft`.
Python documentation string formatting can be found at
https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html

To build the documentation locally, run the following command in a 
command line/PowerShell prompt from the documentation directory::

	make html

HTML files are created in the ``documentation/_build/html`` directory.
Open ``index.html`` to view the documentation.

Examples
---------------------
WNTR includes examples to help new users get started.  
These examples are intended to demonstrate high level features and use cases for WNTR.  
The examples are tested to ensure they stay current with the software project.

Bug reports and feature requests
----------------------------------
Bug reports and feature requests can be submitted to https://github.com/USEPA/WNTR/issues.  
The core development team will prioritize and assign bug reports and feature requests to team members.

.. _contributing:

Contributing
---------------------
Software developers, within the core development team and external collaborators, 
are expected to follow standard practices to document and test new code.  
Software developers interested in contributing to the project are encouraged to 
create a `Fork` of the project and submit a `Pull Request` using GitHub.  
Pull requests will be reviewed by the core development team.  

Pull requests
^^^^^^^^^^^^^
Pull requests can be made to the **main** or **dev** (development) branch.  
Developers can discuss new features and the appropriate branch for contributing 
by opening a new issue on https://github.com/USEPA/WNTR/issues.  

Pull requests must meet the following minimum requirements to be included in WNTR:

* Code is expected to be documented using Read the Docs.  

* Code is expected have sufficient tests.  `Sufficient` is judged by the strength of the test and code coverage. An 80% code coverage is recommended.  

* Large files (> 1Mb) will not be committed to the repository without prior approval.

* Network model files will not be duplicated in the repository.  Network files are stored in examples/network and wntr/tests/networks_for_testing only.

Extensions
^^^^^^^^^^
WNTR extensions are intended to house beta and self-contained functionality that adds to WNTR. 
Developers interested in contributing to WNTR extensions should communicate with the core development team
through https://github.com/USEPA/WNTR/issues prior to submitting a pull request. 
See :ref:`extensions` for a list of current WNTR extensions.

Extensions adhere to the following file structure:
   
* Files associated with the extension, with the exception of documentation and testing, reside in a folder named ``wntr\extensions\<extension_name>``.
* Documentation resides in a file named ``documentation\extensions\<extension_name>.rst``. 
  A link to the documentation should be added to ``documentation\extensions.rst`` and ``documentation\userguide.rst``.
* Testing is run through the `extensions workflow <https://github.com/kaklise/WNTR/blob/swntr/.github/workflows/extensions.yml>`_.
  Tests reside in a file named ``wntr\tests\extensions\test_<extension_name>.py``. 
  Tests should be marked ``@pytest.mark.extensions``.

.. note:: 
   While documentation is required for extensions, the documentation is not included in the 
   `WNTR EPA Report <https://cfpub.epa.gov/si/si_public_record_report.cfm?Lab=NHSRC&dirEntryID=337793>`_.  
   Documentation for extensions is only available online. 
   Extensions that have long term test failures will be removed from the repository.
   
Development team
-------------------
WNTR was developed as part of a collaboration between the United States 
Environmental Protection Agency Office of Research and Development, 
Sandia National Laboratories, and Purdue University.  
See https://github.com/USEPA/WNTR/graphs/contributors for a full list of contributors.