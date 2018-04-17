# NOTES

This file contains information on the VBTS API, programming notes, and other
details.

## Promos

### Currently, there are four (4) promo classes:
* **Discounted** - reduced rates will be made available to a subscriber.
               For example, a promo offer of 2.50 per minute can be availed
               instead of the regular rate of 7.00 per minute.
* **Bulk** - consumable quotas will be offered to a subscriber. These quotas are
         measured in terms of text messages or call minutes that a subscriber
         can make.
* **Unlimited** - A user can make any number of calls or text messages as long
              as the his subscription is still valid.
* **Group Discount** - discounted rates for numbers defined in a group.
                   By default, this group is defined by the subscriber.
                   For example, family and friends promo

### The concept of service types

Communications made by subscribers can be classified into the following
regular service types:

* local_sms
* local_call
* outside_sms
* outside_call

If a subscriber has a valid promo subscription, a "promo type tag" will be
prefixed with any of the following tags:

* 'U_' if unlimited
* 'B_' if bulk
* 'D_' if discounted
* 'G_' if group discount

Thus, if a subscriber has a valid unlimited subscription to local sms, and
he/she makes a local sms, the resulting service type would then be 'U_local_sms'.

These service types are important in order to charge the subscriber correctly.

### Promos with zero fields

If an operator creates a promo and sets any of the fields 'local_sms', 'local_call',
'outside_sms', 'outside_call' values to zero or False, we would use regular rates
to charge the subscriber for the corresponding transaction.

That is we are not allowing the operator to create a promo that would provide
free calls/SMS to the subscriber.

## Limitations on Promo Usage:

* We added configurable parameters that would allow the operator to limit the 
number of promo subscriptions and groups, etc. See the 'Configurable Parameters'
section below for more details.

## Configurable Parameters

* **max_promo_call_duration** - For subscribers with promo subscriptions,
this is the maximum call length (in seconds) that the user can do. Default value
is 180 seconds (3 mins)

* **max_promo_subscription** - Max number of promo subscriptions per subscriber.
Default value is 1.

* **promo_limit_type** - Promo limit type: Possible options: [A, B, NA].
The upper limit on the number of allowed subscriptions is defined by the
key 'max_promo_subscription'. Default value is NA.
  * A - Limit number of subscription per promo
  * B - Limit number of subscription for all promos
  * NA - No Limits
  
* **max_groups_per_subscriber** - Maximum number of groups that a subscriber can
create. Put 'NA' for unlimited. Default value is NA.

* **timezone** - User timezone to be used. Default is 'Asia/Manila'

