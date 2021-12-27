# Sojourner

A mail setup checker for self-hosters

## What does sojourner do?

Sojourner can send emails and check if SPF, DKIM and DMARC are correctly configured.

How does this work? Another email hoster is used that
is known to check SPF/DKIM/DMARC and puts the results
in the Authentication-Result headers. Sojourner checks
these headers to see if our self-hosted email server
is configured correctly.

# More details on how sojourner works

An email is sent to another email hoster, using our 
self-hosted email server. The destination email address
should be configured to forward an email to our
self-hosted email server (probably a different address).
The email is sent back to our self-hosted email server
(if everything goes well!), but with the additional
mail headers that give the result of the SPF/DKIM/DMARC
checks.

Say we have a forward setup from `forward-me@other-email-hoster.tld`
to `healthcheck@our-domain.tld`. Then an email is sent:

    ,-----------.
    | Sojourner |
    `-----------'
      |  1) send email from whatever@our-domain.tld
      v     to forward-me@other-email-hoster.tld
    ,---------------------.
    |  self-hosted SMTP   |
    `---------------------'
      |  2) send email  ^
      v                 |  3) forward email to:
    ,---------------------.   healthcheck@our-domain.tld
    | other email hoster  |
    `---------------------'

After a delay (some hosters take some minutes to
receive/forward emails), the INBOX of the special
account is checked:

    ,-----------.
    | Sojourner |
    `-----------'
      |  1) get emails for healthcheck@our-domain.tld
      v
    ,---------------------.
    |  self-hosted IMAP   |
    `---------------------'

All emails to this address are checked for a special
header that Sojourner added and only emails that were
sent within a certain time (can be configured) are
considered.

If no email was received for a certain sender, then
an error message is shown. If the email headers show
that one of the checks did not pass, an error message
is shown.

# How can Sojourner be used?

There is a docker image that packages this application:
https://hub.docker.com/r/mjholtkamp/sojourner

To configure Sojourner, a settings.py file is mounted in
the docker image. For information on how and what to configure,
see [settings.example.py](conf/settings.example.py)

Then run the following docker command (substituting the path
to the settings file of course):

    docker run \
        -v /path/to/your/settings.py:/app/conf/settings.py \
        mjholtkamp/sojourner \
        send

After a delay, check emails:

    docker run \
        -v /path/to/your/settings.py:/app/conf/settings.py \
        mjholtkamp/sojourner \
        check

I personally have setup two cronjobs to do run these two commands with 10
minutes in between.

# Limitations of Sojourner

 * Sojourner assumes SMTP/IMAP are both accessed over SSL/TLS, so unencrypted access will not work
 * Sojourner only complains if something is not right, you still have to figure out what went wrong in that case
 * Sojourner will not work without a second email hoster, or at least another email server that checks SPF/DKIM/DMARC. Usually that is not checked by the [MSA](https://en.wikipedia.org/wiki/Message_submission_agent), but by the [MTA](https://en.wikipedia.org/wiki/Message_transfer_agent) or [MDA](https://en.wikipedia.org/wiki/Message_delivery_agent).
  * Potentially others that I'm not aware of. Feel free to create an issue if you think it is a bug.

# Why the name Sojourner?

Sojourner is named after [Sojourner Truth](https://en.wikipedia.org/wiki/Sojourner_Truth). I was looking for a famous nurse
(since this application is checking the health :smile:) and when I saw her name, I liked it since it reminded me of the
[Sojourner Mars Rover](https://en.wikipedia.org/wiki/Sojourner_(rover)). I like the name because a sojourner is a traveller
and the emails that Sojourner sends are travelling to and back. Yes, I know the reasons are shallow, but I made this, so I
get to pick the name :wink:.
