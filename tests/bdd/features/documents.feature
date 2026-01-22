Feature: Document Management
  As a veteran
  I want to upload and manage my VA documents
  So that I can get AI-powered analysis of my claims

  Scenario: Document list requires authentication
    Given I am an anonymous user
    When I visit "/claims/"
    Then I should be redirected to the login page

  Scenario: Logged in user can access documents
    Given I am logged in
    When I visit "/claims/"
    Then I should see a 200 status

  Scenario: Upload page requires authentication
    Given I am an anonymous user
    When I visit "/claims/upload/"
    Then I should be redirected to the login page

  Scenario: Logged in user can access upload page
    Given I am logged in
    And I have granted AI consent
    When I visit "/claims/upload/"
    Then I should see a 200 status

  Scenario: Denial decoder requires authentication
    Given I am an anonymous user
    When I visit "/claims/decode/"
    Then I should be redirected to the login page

  Scenario: Logged in user can access denial decoder
    Given I am logged in
    And I have granted AI consent
    When I visit "/claims/decode/"
    Then I should see a 200 status
