Feature: Claims Journey Tracking
  As a veteran
  I want to track my claims journey
  So that I can monitor progress and remember important dates

  Scenario: Journey dashboard requires authentication
    Given I am an anonymous user
    When I visit "/journey/"
    Then I should be redirected to the login page

  Scenario: Logged in user can access journey
    Given I am logged in
    When I visit "/journey/"
    Then I should see a 200 status

  Scenario: Adding milestone requires authentication
    Given I am an anonymous user
    When I visit "/journey/milestone/add/"
    Then I should be redirected to the login page

  Scenario: Logged in user can add milestone
    Given I am logged in
    When I visit "/journey/milestone/add/"
    Then I should see a 200 status

  Scenario: Adding deadline requires authentication
    Given I am an anonymous user
    When I visit "/journey/deadline/add/"
    Then I should be redirected to the login page

  Scenario: Logged in user can add deadline
    Given I am logged in
    When I visit "/journey/deadline/add/"
    Then I should see a 200 status
