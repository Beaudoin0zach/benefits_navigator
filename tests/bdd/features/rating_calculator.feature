Feature: VA Disability Rating Calculator
  As a veteran
  I want to calculate my combined disability rating
  So that I can understand my potential compensation

  Scenario: Rating calculator is publicly accessible
    Given I am an anonymous user
    When I visit "/examprep/rating-calculator/"
    Then I should see a 200 status
    And I should see "Rating Calculator" on the page

  Scenario: SMC calculator is accessible
    Given I am an anonymous user
    When I visit "/examprep/smc-calculator/"
    Then I should see a 200 status

  Scenario: TDIU calculator is accessible
    Given I am an anonymous user
    When I visit "/examprep/tdiu-calculator/"
    Then I should see a 200 status

  Scenario: Premium user can save calculations
    Given I am a premium user
    When I visit "/examprep/rating-calculator/saved/"
    Then I should see a 200 status

  Scenario: Shared calculations are viewable
    Given I am an anonymous user
    When I visit "/examprep/shared/invalid-token/"
    Then I should see a 200 status
