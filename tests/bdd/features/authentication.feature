Feature: User Authentication
  As a veteran
  I want to securely log in and out
  So that I can access my personal claims information

  Background:
    Given I am a registered user

  Scenario: Anonymous user visits protected page
    Given I am an anonymous user
    When I visit "/dashboard/"
    Then I should be redirected to the login page

  Scenario: Successful login
    Given I am an anonymous user
    When I visit "/accounts/login/"
    Then I should see a 200 status
    And I should see "Sign In" on the page

  Scenario: Login with invalid credentials
    Given I am an anonymous user
    When I submit the login form with email "wrong@example.com" and password "wrongpassword"
    Then I should see a 200 status
    And I should see form errors

  Scenario: Public pages are accessible
    Given I am an anonymous user
    When I visit "/"
    Then I should see a 200 status
    And the response should be valid HTML
    And the page should have navigation

  Scenario: Logged in user can access dashboard
    Given I am logged in
    When I visit "/dashboard/"
    Then I should see a 200 status
    And the page should have a main content area
