.. raw:: latex

    \clearpage
	
.. _examples:

Extensions
==========

WNTR extensions are intended to house beta and self-contained functionality that adds to WNTR, 
but is not part of core WNTR development.  

WNTR currently includes the following extension:

- :ref:`stormwater`

Additional extensions will be added at a later date.

.. note:: 
   Software developers interested in contributing to WNTR extensions should communicate with the core development team
   through https://github.com/USEPA/WNTR/issues prior to submitting a pull request.
   See :ref:`developer_instructions` section for more information on contributing to WNTR.
   
   While documentation is required for extensions, the documentation is not included in the 
   `WNTR EPA Report <https://cfpub.epa.gov/si/si_public_record_report.cfm?Lab=NHSRC&dirEntryID=337793>`_.  
   Documentation for extensions is only available online. 
   Testing is run through the ``extensions`` workflow. 
   Extensions that have long term test failures will be removed from the repository.
   
   Extensions use the following structure:
   
   * All files associated with the extension, with the exception of documentation and testing, reside in a folder called ``wntr\extensions\<extension_name>``.
   * Documentation resides in a file called ``documentation\extensions\<extension_name>.rst``. 
     A link to the documentation should be added to ``documentation\extensions.rst`` and ``documentation\userguide.rst``
   * Tests reside in file called ``wntr\tests\test_extensions_<extension_name>.py``. 
     Tests should be marked ``@pytest.mark.extensions``.

Third-party packages
---------------------
User are also encouraged to create third-party software packages that extends functionality in WNTR.  
A list of software packages that build on WNTR is included below:

.. include:: third_party_software.rst
