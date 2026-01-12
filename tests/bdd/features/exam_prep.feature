Feature: C&P Exam Preparation
  As a veteran preparing for a C&P exam
  I want to access preparation guides and checklists
  So that I can be ready for my examination

  Scenario: Exam guides are publicly accessible
    Given I am an anonymous user
    When I visit "/examprep/"
    Then I should see a 200 status
    And the page should have a main content area

  Scenario: Glossary is searchable
    Given I am an anonymous user
    And a glossary term "Nexus Letter" exists
    When I visit "/examprep/glossary/"
    Then I should see a 200 status

  Scenario: Secondary conditions hub is accessible
    Given I am an anonymous user
    When I visit "/examprep/secondary-conditions/"
    Then I should see a 200 status

  Scenario: User checklists require authentication
    Given I am an anonymous user
    When I visit "/examprep/my-checklists/"
    Then I should be redirected to the login page

  Scenario: Logged in user can access checklists
    Given I am logged in
    When I visit "/examprep/my-checklists/"
    Then I should see a 200 status

  Scenario: Creating a checklist requires login
    Given I am an anonymous user
    When I visit "/examprep/my-checklists/create/"
    Then I should be redirected to the login page

  Scenario: Logged in user can create checklist
    Given I am logged in
    When I visit "/examprep/my-checklists/create/"
    Then I should see a 200 status

  Scenario: Evidence checklist is accessible
    Given I am logged in
    When I visit "/examprep/evidence-checklist/"
    Then I should see a 200 status
