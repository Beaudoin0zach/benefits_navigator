Feature: VA Appeals Process
  As a veteran with a denied claim
  I want to understand my appeal options
  So that I can pursue the right path to overturn the decision

  Scenario: Appeals home is publicly accessible
    Given I am an anonymous user
    When I visit "/appeals/"
    Then I should see a 200 status
    And the page should have a main content area

  Scenario: Decision tree is accessible
    Given I am an anonymous user
    When I visit "/appeals/find-your-path/"
    Then I should see a 200 status

  Scenario: My appeals requires authentication
    Given I am an anonymous user
    When I visit "/appeals/my-appeals/"
    Then I should be redirected to the login page

  Scenario: Logged in user can view their appeals
    Given I am logged in
    When I visit "/appeals/my-appeals/"
    Then I should see a 200 status

  Scenario: Starting an appeal requires authentication
    Given I am an anonymous user
    When I visit "/appeals/start/"
    Then I should be redirected to the login page

  Scenario: Logged in user can start an appeal
    Given I am logged in
    When I visit "/appeals/start/"
    Then I should see a 200 status
